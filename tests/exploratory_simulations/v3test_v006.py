"""
Boundary Coherence Across Scales — Computational Study v006
Experiments 1–3: OP 8.1, Assumption 6.3, Coordination Skeleton

Version: 006
Run ID: run006
Base: v3test_v005.py. Changes driven by findings_run005.md and run005 assessment.

CHANGELOG v005 → v006:
  Exp1: m∈{3,4} only, 800 trials per m (1600 random); spectral D_M init (2nd eigenvector
        of symmetrized K) → D_M = max(sampled, fixed, spectral); greedy n=12, E_MIN=1e-22.
  Exp2: Quintiles; dual thresholds 0.20 and 0.10 → collapse_step_020/010, survival by quintile;
        Cox-style: linear reg collapse_step~E0, logistic collapsed~E0 → exp2_cox_style.json.
  Exp3: 5-step skeleton → 11 strategies (Skel 1–5, Rand 1–3, Cen 1–3); full 11×11 pairwise
        win matrix; frac E_final < 0.005 and < 0.001; Skel k vs Cen k / Rand k for k=1..5.
  All outputs to docs/exploratory_simulations/run006/.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import eigvals, eigh
import warnings
import json
import time

warnings.filterwarnings("ignore")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

RUN_ID = "006"
OUTPUT_DIR = Path(__file__).resolve().parent / "run006"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
t_run_start = time.time()

# ── Core Machinery ─────────────────────────────────────────────────────────────


def random_kernel(n, c=1.0):
    return np.random.dirichlet([c] * n, size=n)


def stationary(K):
    n = K.shape[0]
    A = K.T - np.eye(n)
    A[-1] = 1.0
    b = np.zeros(n)
    b[-1] = 1.0
    try:
        pi = np.linalg.solve(A, b)
        pi = np.maximum(pi, 0)
        pi /= pi.sum() + 1e-16
    except np.linalg.LinAlgError:
        pi = np.ones(n) / n
    return pi


def L2_proj(partition, pi, n):
    Pi = np.zeros((n, n))
    for block in partition:
        if not block:
            continue
        b = list(block)
        mass = pi[b].sum()
        if mass < 1e-14:
            continue
        for i in b:
            for j in b:
                Pi[i, j] = pi[j] / mass
    return Pi


def closure_energy(K, Pi, pi):
    n = K.shape[0]
    Kq = (np.eye(n) - Pi) @ K @ Pi
    D = np.diag(pi)
    Dinv = np.diag(1.0 / (pi + 1e-15))
    return float(np.trace(Kq.T @ D @ Kq @ Dinv))


def abs_gap(K, pi):
    n = K.shape[0]
    sqrt_pi = np.sqrt(pi + 1e-15)
    D = np.diag(sqrt_pi)
    Dinv = np.diag(1.0 / sqrt_pi)
    sym_K = D @ K @ Dinv
    ev = np.sort(np.abs(np.real(eigvals(sym_K))))[::-1]
    return float(1.0 - ev[1]) if len(ev) > 1 else 1.0


def random_partition(n, m):
    if m < 1 or m > n:
        m = np.random.randint(1, n + 1)
    labels = np.zeros(n, dtype=int)
    labels[:m] = np.arange(m)
    labels[m:] = np.random.randint(0, m, size=n - m)
    np.random.shuffle(labels)
    partition = [set(np.where(labels == k)[0]) for k in range(m)]
    return [b for b in partition if b]


def proj_dist(Pa, Pb, pi):
    d = Pa - Pb
    return float(np.sqrt(np.trace(d.T @ np.diag(pi) @ d)))


def fixed_coarse_diameter(pi, n):
    if n < 2:
        return 0.0
    ks = [max(1, n // 4), n // 2, min(n - 1, 3 * n // 4)]
    ks = sorted(set(ks))
    partitions = []
    for k in ks:
        q = [set(range(k)), set(range(k, n))]
        partitions.append(q)
    best = 0.0
    for i in range(len(partitions)):
        for j in range(i + 1, len(partitions)):
            Pi_i = L2_proj(partitions[i], pi, n)
            Pi_j = L2_proj(partitions[j], pi, n)
            d = proj_dist(Pi_i, Pi_j, pi)
            if d > best:
                best = d
    return best


def spectral_2block_partition(K, pi, n):
    """v006: 2-block partition from 2nd eigenvector of symmetrized K (spectral clustering)."""
    sqrt_pi = np.sqrt(pi + 1e-15)
    D = np.diag(sqrt_pi)
    Dinv = np.diag(1.0 / sqrt_pi)
    sym_K = D @ K @ Dinv
    try:
        w, v = eigh(sym_K)
        idx = np.argsort(w)[::-1]
        v2 = v[:, idx[1]]
        labels = (v2 >= np.median(v2)).astype(int)
        if np.sum(labels) == 0 or np.sum(labels) == n:
            labels = (v2 >= 0).astype(int)
        return [set(np.where(labels == 0)[0]), set(np.where(labels == 1)[0])]
    except Exception:
        return [set(range(n // 2)), set(range(n // 2, n))]


def spectral_diameter(K, pi, n):
    """v006: max proj_dist from spectral 2-block partition to canonical 2-block splits."""
    q_spec = spectral_2block_partition(K, pi, n)
    Pi_spec = L2_proj(q_spec, pi, n)
    best = 0.0
    for k in [max(1, n // 4), n // 2, min(n - 1, 3 * n // 4)]:
        q_can = [set(range(k)), set(range(k, n))]
        Pi_can = L2_proj(q_can, pi, n)
        d = proj_dist(Pi_spec, Pi_can, pi)
        if d > best:
            best = d
    return best


def mis_sampled(pi, n, m=2, S=200):
    best = np.inf
    for _ in range(S):
        qa = random_partition(n, m)
        qb = random_partition(n, m)
        d = proj_dist(L2_proj(qa, pi, n), L2_proj(qb, pi, n), pi)
        if d < best:
            best = d
        if np.random.rand() < 0.15:
            m_alt = np.random.choice([max(2, m - 1), m + 1]) if m + 1 <= n else m
            qa = random_partition(n, m_alt)
            qb = random_partition(n, m_alt)
            d = proj_dist(L2_proj(qa, pi, n), L2_proj(qb, pi, n), pi)
            if d < best:
                best = d
    return best


def greedy_coarsegrain(K, pi, n, max_merges=None):
    partition = [{i} for i in range(n)]
    current_Pi = L2_proj(partition, pi, n)
    current_E = closure_energy(K, current_Pi, pi)
    while len(partition) > 1:
        best_delta = np.inf
        best_i, best_j = -1, -1
        for i in range(len(partition)):
            for j in range(i + 1, len(partition)):
                new_block = partition[i] | partition[j]
                new_part = [partition[k] for k in range(len(partition)) if k not in (i, j)] + [new_block]
                new_Pi = L2_proj(new_part, pi, n)
                new_E = closure_energy(K, new_Pi, pi)
                delta = new_E - current_E
                if delta < best_delta:
                    best_delta = delta
                    best_i, best_j = i, j
        if best_delta > 1e-9 or best_i < 0:
            break
        new_block = partition[best_i] | partition[best_j]
        partition = [partition[k] for k in range(len(partition)) if k not in (best_i, best_j)] + [new_block]
        current_Pi = L2_proj(partition, pi, n)
        current_E = closure_energy(K, current_Pi, pi)
        if len(partition) <= 2:
            break
    return partition


# ── EXPERIMENT 1: m=3,4 only × 800, spectral D_M; greedy n=12, E_MIN=1e-22 ──

print("=" * 70)
print("EXPERIMENT 1: OP 8.1 — m=3,4 × 800, spectral D_M, greedy n=12 (v006)")
print("=" * 70)

DM_MIN, K2_MIN, G_MIN = 1e-14, 1e-12, 1e-12
E_MIN_RANDOM, E_MIN_GREEDY = 1e-14, 1e-22
n, n_greedy, n_ag = 10, 12, 3
N_PER_M, M_VALS = 800, [3, 4]
N1_RANDOM = N_PER_M * len(M_VALS)
N1_GREEDY = 500
MIS_SAMPLES = 200

t0 = time.time()
results_1 = []
drop_reasons = {"DM": 0, "K2": 0, "gap": 0, "E": 0, "ok_random": 0, "ok_greedy": 0}

for trial in range(N1_RANDOM):
    Ks = [random_kernel(n, c=np.random.uniform(0.3, 3.0)) for _ in range(n_ag)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    K2 = float(np.einsum("ij,i,ij->", Kj, pi, Kj))
    m = M_VALS[trial % len(M_VALS)]
    q_star = random_partition(n, m=m)
    Pi_star = L2_proj(q_star, pi, n)
    E = closure_energy(Kj, Pi_star, pi)
    g = abs_gap(Kj, pi)
    d_sampled = mis_sampled(pi, n, m=2, S=MIS_SAMPLES)
    d_fixed = fixed_coarse_diameter(pi, n)
    d_spectral = spectral_diameter(Kj, pi, n)
    DM = max(d_sampled, d_fixed, d_spectral)
    if DM <= DM_MIN or K2 <= K2_MIN or g <= G_MIN or E <= E_MIN_RANDOM:
        if E <= E_MIN_RANDOM:
            drop_reasons["E"] += 1
        else:
            drop_reasons["DM"] += 1
    else:
        drop_reasons["ok_random"] += 1
        results_1.append({
            "trial": trial, "q_mode": "random", "m_blocks": m,
            "E_cl": E, "D_M": DM, "D_M_spectral": d_spectral, "gap": g, "K2": K2, "n_blocks": len(q_star),
            "ratio_T32": E / (DM ** 2 * K2 + 1e-20),
            "ratio_81": E / (DM * g * K2 + 1e-20),
            "ratio_norm": E / (DM * K2 + 1e-20),
        })

for trial in range(N1_GREEDY):
    Ks = [random_kernel(n_greedy, c=np.random.uniform(0.3, 3.0)) for _ in range(n_ag)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    K2 = float(np.einsum("ij,i,ij->", Kj, pi, Kj))
    q_star = greedy_coarsegrain(Kj, pi, n_greedy)
    Pi_star = L2_proj(q_star, pi, n_greedy)
    E = closure_energy(Kj, Pi_star, pi)
    g = abs_gap(Kj, pi)
    d_sampled = mis_sampled(pi, n_greedy, m=2, S=MIS_SAMPLES)
    d_fixed = fixed_coarse_diameter(pi, n_greedy)
    d_spectral = spectral_diameter(Kj, pi, n_greedy)
    DM = max(d_sampled, d_fixed, d_spectral)
    if DM <= DM_MIN or K2 <= K2_MIN or g <= G_MIN or E <= E_MIN_GREEDY:
        drop_reasons["E"] += 1
    else:
        drop_reasons["ok_greedy"] += 1
        results_1.append({
            "trial": N1_RANDOM + trial, "q_mode": "greedy", "m_blocks": len(q_star), "n": n_greedy,
            "E_cl": E, "D_M": DM, "D_M_spectral": d_spectral, "gap": g, "K2": K2, "n_blocks": len(q_star),
            "ratio_T32": E / (DM ** 2 * K2 + 1e-20),
            "ratio_81": E / (DM * g * K2 + 1e-20),
            "ratio_norm": E / (DM * K2 + 1e-20),
        })

df1 = pd.DataFrame(results_1)
df1.to_csv(OUTPUT_DIR / "exp1_op81.csv", index=False)
(OUTPUT_DIR / "exp1_drop_reasons.json").write_text(json.dumps(drop_reasons, indent=2))

exp1_summary = []
for mode in ["random", "greedy"]:
    sub = df1[df1["q_mode"] == mode]
    if len(sub) == 0:
        continue
    exp1_summary.append({
        "q_mode": mode, "n_trials": len(sub),
        "ratio_81_max": float(sub["ratio_81"].max()), "ratio_81_mean": float(sub["ratio_81"].mean()),
        "ratio_81_median": float(sub["ratio_81"].median()), "c_star_approx": float(1.0 / (sub["ratio_81"].max() + 1e-20)),
    })
for m in M_VALS:
    sub = df1[(df1["q_mode"] == "random") & (df1["m_blocks"] == m)]
    if len(sub) == 0:
        continue
    exp1_summary.append({
        "q_mode": "random", "m_blocks": m, "n_trials": len(sub),
        "ratio_81_max": float(sub["ratio_81"].max()), "ratio_81_mean": float(sub["ratio_81"].mean()),
    })
pd.DataFrame(exp1_summary).to_csv(OUTPUT_DIR / "exp1_summary_by_mode.csv", index=False)

print(f"Trials: random {N1_RANDOM} (m=3,4 x800), greedy {N1_GREEDY} (n=12)  |  Retained: {len(df1)}  |  Time: {time.time() - t0:.1f}s")
print("Drop reasons:", drop_reasons)
if len(df1) > 0:
    for mode in ["random", "greedy"]:
        sub = df1[df1["q_mode"] == mode]
        if len(sub) > 0:
            print(f"  {mode}: n={len(sub)}  ratio_81 max={sub['ratio_81'].max():.4f}  mean={sub['ratio_81'].mean():.4f}  c*≈{1.0/(sub['ratio_81'].max()+1e-20):.4f}")
    for m in M_VALS:
        sub = df1[(df1["q_mode"] == "random") & (df1["m_blocks"] == m)]
        if len(sub) > 0:
            print(f"  random m={m}: n={len(sub)}  ratio_81 max={sub['ratio_81'].max():.4f}  mean={sub['ratio_81'].mean():.4f}")

if HAS_MPL and len(df1) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, mode in zip(axes, ["random", "greedy"]):
        sub = df1[df1["q_mode"] == mode]
        if len(sub) > 0:
            ax.hist(sub["ratio_81"].clip(upper=sub["ratio_81"].quantile(0.99)), bins=40, edgecolor="k", alpha=0.7)
        ax.set_xlabel("ratio_81")
        ax.set_ylabel("Count")
        ax.set_title(f"Exp1 {mode} (v006)")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "exp1_ratio81_hist_by_mode.png", dpi=120)
    plt.close(fig)

# ── EXPERIMENT 2: Quintiles, dual threshold (0.20, 0.10), Cox-style hazard ──

print("\n" + "=" * 70)
print("EXPERIMENT 2: Assumption 6.3 — Quintiles, dual threshold, Cox-style (v006)")
print("=" * 70)

n2, N2 = 8, 500
collapse_thresh_high, collapse_thresh_low = 0.20, 0.10
max_steps = 50
perturb_str = 0.35

t0 = time.time()
results_2 = []
E_trajectories = []

for trial in range(N2):
    c_val = np.random.uniform(0.1, 5.0)
    K0 = random_kernel(n2, c=c_val)
    pi0 = stationary(K0)
    q0 = random_partition(n2, 2)
    Pi0 = L2_proj(q0, pi0, n2)
    E0 = closure_energy(K0, Pi0, pi0)
    g0 = abs_gap(K0, pi0)
    Kc = K0.copy()
    collapse_step_high = max_steps
    collapse_step_low = max_steps
    E_trajectory = [E0]
    for step in range(1, max_steps + 1):
        noise = random_kernel(n2, c=1.0)
        Kc = (1 - perturb_str) * Kc + perturb_str * noise
        Kc /= Kc.sum(axis=1, keepdims=True) + 1e-15
        pic = stationary(Kc)
        Pic = L2_proj(q0, pic, n2)
        Ec = closure_energy(Kc, Pic, pic)
        E_trajectory.append(Ec)
        if Ec > collapse_thresh_high and collapse_step_high == max_steps:
            collapse_step_high = step
        if Ec > collapse_thresh_low and collapse_step_low == max_steps:
            collapse_step_low = step
    results_2.append({
        "trial": trial, "E0": E0, "g0": g0, "c_val": c_val,
        "collapse_step": collapse_step_low,
        "collapse_step_020": collapse_step_high,
        "collapse_step_010": collapse_step_low,
        "collapsed_020": collapse_step_high < max_steps,
        "collapsed_010": collapse_step_low < max_steps,
        "E_final": E_trajectory[-1],
    })
    E_trajectories.append(E_trajectory)

df2 = pd.DataFrame(results_2)
df2["E0_quintile"] = pd.qcut(df2["E0"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates="drop")
quintile_labels = ["Q1", "Q2", "Q3", "Q4", "Q5"]
grp2_q = df2.groupby("E0_quintile", observed=True).agg(
    collapse_rate_010=("collapsed_010", "mean"),
    collapse_rate_020=("collapsed_020", "mean"),
    mean_steps=("collapse_step_010", "mean"),
    mean_E0=("E0", "mean"),
).reset_index()
grp2_q.to_csv(OUTPUT_DIR / "exp2_quintiles.csv", index=False)

r_q1 = grp2_q[grp2_q["E0_quintile"] == "Q1"]["collapse_rate_010"].values
r_q5 = grp2_q[grp2_q["E0_quintile"] == "Q5"]["collapse_rate_010"].values
hr_q5_vs_q1 = (float(r_q5[0]) + 1e-6) / (float(r_q1[0]) + 1e-6) if len(r_q1) and len(r_q5) else np.nan
dual_hr = {
    "threshold_020": {"collapse_rate_overall": float(df2["collapsed_020"].mean())},
    "threshold_010": {"collapse_rate_overall": float(df2["collapsed_010"].mean())},
    "hazard_ratio_Q5_vs_Q1_010": hr_q5_vs_q1,
}
(OUTPUT_DIR / "exp2_hazard_ratio_quintiles.json").write_text(json.dumps(dual_hr, indent=2))

# Cox-style: linear reg collapse_step ~ E0; odds ratio (E0 high vs low vs collapsed)
from scipy import stats
y_step = df2["collapse_step_010"].values
x_e0 = df2["E0"].values
slope, intercept, r_val, p_val, se = stats.linregress(x_e0, y_step)
med_e0 = df2["E0"].median()
high_e0 = (df2["E0"] >= med_e0).values
collapsed = df2["collapsed_010"].values
a = np.sum(high_e0 & collapsed)
b = np.sum(high_e0 & ~collapsed)
c = np.sum(~high_e0 & collapsed)
d = np.sum(~high_e0 & ~collapsed)
odds_ratio_high_vs_low = (a * d) / (b * c + 1e-10)
cox_report = {
    "linear_collapse_step_E0": {"slope": float(slope), "r": float(r_val), "p": float(p_val)},
    "odds_ratio_highE0_vs_lowE0_collapse": float(odds_ratio_high_vs_low),
}
(OUTPUT_DIR / "exp2_cox_style.json").write_text(json.dumps(cox_report, indent=2))

corr_E0_steps = df2["E0"].corr(df2["collapse_step_010"])
survival_rows = []
for step in range(max_steps + 1):
    row = {"step": step}
    for q in quintile_labels:
        mask = df2["E0_quintile"] == q
        if mask.sum() == 0:
            row[q] = np.nan
            continue
        survived = sum(1 for i in df2.index[mask] if step < len(E_trajectories[i]) and E_trajectories[i][step] <= collapse_thresh_low)
        row[q] = survived / max(1, mask.sum())
    survival_rows.append(row)
df_survival = pd.DataFrame(survival_rows)
df_survival.to_csv(OUTPUT_DIR / "exp2_survival_by_quintile.csv", index=False)
df2.to_csv(OUTPUT_DIR / "exp2_hazard.csv", index=False)

print(f"Trials: {len(df2)}  |  Time: {time.time() - t0:.1f}s")
print("Quintiles (collapse @ 0.10):")
print(grp2_q.to_string(index=False))
print(f"\nCorrelation r(E0, collapse_step_010): {corr_E0_steps:.4f}")
print(f"Hazard ratio Q5/Q1 (thresh 0.10): {hr_q5_vs_q1:.2f}")
print(f"Cox-style: slope(collapse_step~E0)={slope:.4f}, r={r_val:.4f}")

if HAS_MPL:
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    for q in quintile_labels:
        if q in df_survival.columns:
            ax.plot(df_survival["step"], df_survival[q], label=q)
    ax.set_xlabel("Step")
    ax.set_ylabel("Fraction surviving (E ≤ 0.10)")
    ax.set_title("Exp2 Survival by E0 quintile (v006)")
    ax.legend()
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "exp2_survival_curves_quintiles.png", dpi=120)
    plt.close(fig)

# ── EXPERIMENT 3: 5-step skeleton, 11 strategies, full pairwise, E_final 0.005/0.001 ──

print("\n" + "=" * 70)
print("EXPERIMENT 3: Coordination Skeleton (v006: 5-step, 11 strategies, full pairwise)")
print("=" * 70)

n3, nag3, N3 = 8, 6, 500
MIS_S3 = 100
E_THRESHOLD_001, E_THRESHOLD_0005, E_THRESHOLD_0001 = 0.01, 0.005, 0.001

t0 = time.time()
results_3 = []

def align_measure(Ks_list, part, align_i, align_j):
    Kn = [k.copy() for k in Ks_list]
    Kn[align_j] = 0.5 * Kn[align_i] + 0.5 * Kn[align_j]
    Kn[align_j] /= Kn[align_j].sum(axis=1, keepdims=True) + 1e-15
    Kjn = np.mean(Kn, axis=0)
    pin = stationary(Kjn)
    Pin = L2_proj(part, pin, n3)
    return closure_energy(Kjn, Pin, pin), Kn

for trial in range(N3):
    Ks = [random_kernel(n3, c=np.random.uniform(0.5, 2.0)) for _ in range(nag3)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    q = random_partition(n3, 2)
    Pi = L2_proj(q, pi, n3)
    E0 = closure_energy(Kj, Pi, pi)
    M = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            mij = mis_sampled(pi, n3, m=2, S=MIS_S3)
            M[i, j] = M[j, i] = mij
    wi, wj = np.unravel_index(np.triu(M, 1).argmax(), M.shape)
    pairs = [(i, j) for i in range(nag3) for j in range(i + 1, nag3)]
    ri, rj = pairs[np.random.randint(len(pairs))]
    cen = M.sum(axis=1)
    ci = int(np.argmax(cen))
    row = M[ci].copy()
    row[ci] = -np.inf
    cj = int(np.argmax(row))

    # Skeleton 1–5 step
    E_A1, Kn1 = align_measure(Ks, q, wi, wj)
    Kn_cur = Kn1
    E_A2 = E_A3 = E_A4 = E_A5 = E_A1
    for step in range(2, 6):
        pin_cur = stationary(np.mean(Kn_cur, axis=0))
        M_cur = np.zeros((nag3, nag3))
        for i in range(nag3):
            for j in range(i + 1, nag3):
                M_cur[i, j] = M_cur[j, i] = mis_sampled(pin_cur, n3, m=2, S=50)
        wi_s, wj_s = np.unravel_index(np.triu(M_cur, 1).argmax(), M_cur.shape)
        E_new, Kn_cur = align_measure(Kn_cur, q, wi_s, wj_s)
        if step == 2: E_A2 = E_new
        elif step == 3: E_A3 = E_new
        elif step == 4: E_A4 = E_new
        else: E_A5 = E_new

    E_B1, Kn_r1 = align_measure(Ks, q, ri, rj)
    ri2, rj2 = pairs[np.random.randint(len(pairs))]
    E_B2, Kn_r2 = align_measure(Kn_r1, q, ri2, rj2)
    ri3, rj3 = pairs[np.random.randint(len(pairs))]
    E_B3, _ = align_measure(Kn_r2, q, ri3, rj3)
    E_C1, Kn_c1 = align_measure(Ks, q, ci, cj)
    pin_c1 = stationary(np.mean(Kn_c1, axis=0))
    Mc1 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            Mc1[i, j] = Mc1[j, i] = mis_sampled(pin_c1, n3, m=2, S=30)
    ci2 = int(np.argmax(Mc1.sum(axis=1)))
    row_c1 = Mc1[ci2].copy(); row_c1[ci2] = -np.inf; cj2 = int(np.argmax(row_c1))
    E_C2, Kn_c2 = align_measure(Kn_c1, q, ci2, cj2)
    pin_c2 = stationary(np.mean(Kn_c2, axis=0))
    Mc2 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            Mc2[i, j] = Mc2[j, i] = mis_sampled(pin_c2, n3, m=2, S=30)
    ci3 = int(np.argmax(Mc2.sum(axis=1)))
    row_c2 = Mc2[ci3].copy(); row_c2[ci3] = -np.inf; cj3 = int(np.argmax(row_c2))
    E_C3, _ = align_measure(Kn_c2, q, ci3, cj3)

    d = {
        "E0": E0,
        "dE_skeleton_1": E0 - E_A1, "dE_skeleton_2": E0 - E_A2, "dE_skeleton_3": E0 - E_A3, "dE_skeleton_4": E0 - E_A4, "dE_skeleton_5": E0 - E_A5,
        "dE_random_1": E0 - E_B1, "dE_random_2": E0 - E_B2, "dE_random_3": E0 - E_B3,
        "dE_centrality_1": E0 - E_C1, "dE_centrality_2": E0 - E_C2, "dE_centrality_3": E0 - E_C3,
        "E_final_skel_1": E_A1, "E_final_skel_2": E_A2, "E_final_skel_3": E_A3, "E_final_skel_4": E_A4, "E_final_skel_5": E_A5,
        "E_final_random_1": E_B1, "E_final_random_2": E_B2, "E_final_random_3": E_B3,
        "E_final_centrality_1": E_C1, "E_final_centrality_2": E_C2, "E_final_centrality_3": E_C3,
    }
    results_3.append(d)

df3 = pd.DataFrame(results_3)
df3.to_csv(OUTPUT_DIR / "exp3_skeleton.csv", index=False)

STRATEGY_NAMES = ["Skel 1", "Skel 2", "Skel 3", "Skel 4", "Skel 5", "Rand 1", "Rand 2", "Rand 3", "Cen 1", "Cen 2", "Cen 3"]
dE_cols = ["dE_skeleton_1", "dE_skeleton_2", "dE_skeleton_3", "dE_skeleton_4", "dE_skeleton_5", "dE_random_1", "dE_random_2", "dE_random_3", "dE_centrality_1", "dE_centrality_2", "dE_centrality_3"]
E_cols = ["E_final_skel_1", "E_final_skel_2", "E_final_skel_3", "E_final_skel_4", "E_final_skel_5", "E_final_random_1", "E_final_random_2", "E_final_random_3", "E_final_centrality_1", "E_final_centrality_2", "E_final_centrality_3"]
max_dE_per_row = df3[dE_cols].max(axis=1)

# Full 11×11 pairwise win matrix
pairwise_matrix = []
for i, name_a in enumerate(STRATEGY_NAMES):
    row = {"strategy": name_a}
    for j, name_b in enumerate(STRATEGY_NAMES):
        if i == j:
            row[name_b] = 0.5
        else:
            p_a_wins = (df3[dE_cols[i]] > df3[dE_cols[j]]).mean()
            row[name_b] = round(float(p_a_wins), 4)
    pairwise_matrix.append(row)
pd.DataFrame(pairwise_matrix).to_csv(OUTPUT_DIR / "exp3_pairwise_matrix_11x11.csv", index=False)

# Skel k vs Cen k and Skel k vs Rand k for k=1..5
skel_vs = []
for k in range(1, 6):
    skel_col = f"dE_skeleton_{k}"
    cen_col = f"dE_centrality_{k}" if k <= 3 else "dE_centrality_3"
    rand_col = f"dE_random_{k}" if k <= 3 else "dE_random_3"
    skel_vs.append({"k": k, "p_skel_gt_cen": float((df3[skel_col] > df3[cen_col]).mean()), "p_skel_gt_rand": float((df3[skel_col] > df3[rand_col]).mean())})
pd.DataFrame(skel_vs).to_csv(OUTPUT_DIR / "exp3_skel_k_vs_cen_rand.csv", index=False)

# Strategy summary with frac E < 0.01, 0.005, 0.001
summary_rows = []
for lab, dE_col, E_col in [
    ("Skel 1", "dE_skeleton_1", "E_final_skel_1"), ("Skel 2", "dE_skeleton_2", "E_final_skel_2"), ("Skel 3", "dE_skeleton_3", "E_final_skel_3"), ("Skel 4", "dE_skeleton_4", "E_final_skel_4"), ("Skel 5", "dE_skeleton_5", "E_final_skel_5"),
    ("Rand 1", "dE_random_1", "E_final_random_1"), ("Rand 2", "dE_random_2", "E_final_random_2"), ("Rand 3", "dE_random_3", "E_final_random_3"),
    ("Cen 1", "dE_centrality_1", "E_final_centrality_1"), ("Cen 2", "dE_centrality_2", "E_final_centrality_2"), ("Cen 3", "dE_centrality_3", "E_final_centrality_3"),
]:
    best_pct = (df3[dE_col] >= max_dE_per_row - 1e-12).mean()
    summary_rows.append({
        "strategy": lab,
        "mean_dE": float(df3[dE_col].mean()),
        "std_dE": float(df3[dE_col].std()),
        "frac_E_below_001": float((df3[E_col] < E_THRESHOLD_001).mean()),
        "frac_E_below_0005": float((df3[E_col] < E_THRESHOLD_0005).mean()),
        "frac_E_below_0001": float((df3[E_col] < E_THRESHOLD_0001).mean()),
        "best_overall_pct": float(best_pct),
    })
pd.DataFrame(summary_rows).to_csv(OUTPUT_DIR / "exp3_strategy_summary.csv", index=False)

box_rows = []
for _, r in df3.iterrows():
    for lab, col in zip(STRATEGY_NAMES, dE_cols):
        box_rows.append({"strategy": lab, "dE": r[col]})
box_df = pd.DataFrame(box_rows)
box_df.to_csv(OUTPUT_DIR / "exp3_boxplot_data.csv", index=False)
if HAS_MPL:
    fig, ax = plt.subplots(1, 1, figsize=(14, 4))
    data = [box_df.loc[box_df["strategy"] == s, "dE"].values for s in STRATEGY_NAMES]
    ax.boxplot(data, labels=STRATEGY_NAMES, patch_artist=True)
    ax.set_ylabel("ΔE_cl")
    ax.set_title("Exp3 ΔE_cl by strategy (v006, 11 strategies)")
    plt.xticks(rotation=25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "exp3_boxplot_dE.png", dpi=120)
    plt.close(fig)

print(f"Trials: {len(df3)}  |  Time: {time.time() - t0:.1f}s")
print("\nStrategy summary (mean_dE, frac E<0.005, E<0.001, best_pct):")
print(pd.DataFrame(summary_rows)[["strategy", "mean_dE", "frac_E_below_0005", "frac_E_below_0001", "best_overall_pct"]].to_string(index=False))
print("\nSkel k vs Cen k / Rand k:")
print(pd.DataFrame(skel_vs).to_string(index=False))

# ── Run summary ──

total_elapsed = time.time() - t_run_start
run_summary = {
    "run_id": RUN_ID,
    "script": "v3test_v006.py",
    "exp1": {"N1_random": N1_RANDOM, "N1_greedy": N1_GREEDY, "n": n, "n_greedy": n_greedy, "retained": len(df1), "drop_reasons": drop_reasons},
    "exp2": {"N2": N2, "perturb_str": perturb_str, "max_steps": max_steps, "collapse_thresh_010": collapse_thresh_low, "collapse_thresh_020": collapse_thresh_high, "collapse_rate_010": float(df2["collapsed_010"].mean()), "hazard_ratio_Q5_vs_Q1": hr_q5_vs_q1},
    "exp3": {"N3": N3, "n3": n3, "nag3": nag3, "n_strategies": 11, "skel_5step_mean_dE": float(df3["dE_skeleton_5"].mean())},
    "output_dir": str(OUTPUT_DIR),
    "total_elapsed_sec": round(total_elapsed, 1),
}
(OUTPUT_DIR / "run_summary.json").write_text(json.dumps(run_summary, indent=2))
print("\nRun summary written to", OUTPUT_DIR / "run_summary.json")
print("Outputs:", sorted([p.name for p in OUTPUT_DIR.iterdir()]))
