"""
Boundary Coherence Across Scales — Computational Study v004
Experiments 1–3: OP 8.1, Assumption 6.3, Coordination Skeleton

Version: 004
Run ID: run004
Base: v3test_v003.py. Changes driven by findings_run003.md and run003 interpretation.

CHANGELOG v003 → v004:
  Exp1: q_star = random_partition(n, m=3) instead of greedy_coarsegrain so E_cl is in
        higher range (0.001–0.2); expect 500–1500 valid trials and first real OP 8.1 ratios.
  Exp2: perturb_str 0.28→0.32, max_steps 40→50; export survival-by-step by E0 quartile;
        optional Kaplan–Meier-style plot.
  Exp3: 3-step skeleton; 2-step and 3-step baselines for random and centrality;
        report skel_3step_best, fraction E_final < 0.01 per strategy; boxplot data.
  Plots: hist of ratio_81 (Exp1), survival curves (Exp2), boxplots ΔE by strategy (Exp3).
  All outputs to docs/exploratory_simulations/run004/.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import eigvals
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

RUN_ID = "004"
OUTPUT_DIR = Path(__file__).resolve().parent / "run004"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
t_run_start = time.time()

# ── Core Machinery ─────────────────────────────────────────────────────────────


def random_kernel(n, c=1.0):
    """Dirichlet-sampled stochastic matrix"""
    return np.random.dirichlet([c] * n, size=n)


def stationary(K):
    """Solve for left eigenvector with eigenvalue 1"""
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
    """L² projection matrix onto partition blocks"""
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
    """Closure energy: pi-weighted Frobenius-like norm of leakage operator"""
    n = K.shape[0]
    Kq = (np.eye(n) - Pi) @ K @ Pi
    D = np.diag(pi)
    Dinv = np.diag(1.0 / (pi + 1e-15))
    return float(np.trace(Kq.T @ D @ Kq @ Dinv))


def abs_gap(K, pi):
    """Absolute spectral gap using symmetrized operator"""
    n = K.shape[0]
    sqrt_pi = np.sqrt(pi + 1e-15)
    D = np.diag(sqrt_pi)
    Dinv = np.diag(1.0 / sqrt_pi)
    sym_K = D @ K @ Dinv
    ev = np.sort(np.abs(np.real(eigvals(sym_K))))[::-1]
    return float(1.0 - ev[1]) if len(ev) > 1 else 1.0


def random_partition(n, m):
    """Generate random non-empty partition into exactly m blocks"""
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
    """Max pairwise L2 projection distance over canonical 2-block splits."""
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


def mis_sampled(pi, n, m=2, S=200):
    """Estimate of inf ||Π_qa - Π_qb|| over partitions into m blocks"""
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


# ── EXPERIMENT 1: OP 8.1 with random partition (v004: unblock validity) ──

print("=" * 70)
print("EXPERIMENT 1: Open Problem 8.1 — Lower Bound (v004: random q_star)")
print("=" * 70)

DM_MIN, K2_MIN, G_MIN, E_MIN = 1e-14, 1e-12, 1e-12, 1e-14
n, n_ag, N1 = 10, 3, 2000
MIS_SAMPLES = 200
EXP1_M_BLOCKS = 3   # v004: fixed 2–3 block random partition instead of greedy

t0 = time.time()
results_1 = []
drop_reasons = {"DM": 0, "K2": 0, "gap": 0, "E": 0, "ok": 0}

for trial in range(N1):
    Ks = [random_kernel(n, c=np.random.uniform(0.3, 3.0)) for _ in range(n_ag)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    K2 = float(np.einsum("ij,i,ij->", Kj, pi, Kj))

    # v004: random partition so E_cl is in higher, variable range (conservative bound test)
    q_star = random_partition(n, m=EXP1_M_BLOCKS)
    Pi_star = L2_proj(q_star, pi, n)
    E = closure_energy(Kj, Pi_star, pi)
    g = abs_gap(Kj, pi)

    d_sampled = mis_sampled(pi, n, m=2, S=MIS_SAMPLES)
    d_fixed = fixed_coarse_diameter(pi, n)
    DM = max(d_sampled, d_fixed)

    if DM <= DM_MIN:
        drop_reasons["DM"] += 1
    elif K2 <= K2_MIN:
        drop_reasons["K2"] += 1
    elif g <= G_MIN:
        drop_reasons["gap"] += 1
    elif E <= E_MIN:
        drop_reasons["E"] += 1
    else:
        drop_reasons["ok"] += 1
        results_1.append({
            "trial": trial,
            "E_cl": E, "D_M": DM, "D_M_sampled": d_sampled, "D_M_fixed": d_fixed,
            "gap": g, "K2": K2,
            "n_blocks": len(q_star),
            "ratio_T32": E / (DM ** 2 * K2 + 1e-20),
            "ratio_81": E / (DM * g * K2 + 1e-20),
            "ratio_norm": E / (DM * K2 + 1e-20),
        })

df1 = pd.DataFrame(results_1)
path1 = OUTPUT_DIR / "exp1_op81.csv"
df1.to_csv(path1, index=False)
(OUTPUT_DIR / "exp1_drop_reasons.json").write_text(json.dumps(drop_reasons, indent=2))

print(f"Trials: {N1}  |  Retained: {len(df1)}  |  Time: {time.time() - t0:.1f}s")
print("Drop reasons:", drop_reasons)
if len(df1) > 0:
    print(f"\nT3.2 — E_cl/(D_M² K²)   max: {df1.ratio_T32.max():.4f}  mean: {df1.ratio_T32.mean():.4f}")
    print(f"Violations >1: {(df1.ratio_T32 > 1.0).sum()}")
    print(f"\nOP 8.1 — E_cl/(D_M·gap·K²)   max: {df1.ratio_81.max():.4f}  mean: {df1.ratio_81.mean():.4f}")
    print(f"Empirical c* ≈ {1.0 / (df1.ratio_81.max() + 1e-20):.4f}")
    print(f"D_M stats: mean={df1['D_M'].mean():.6f}")
else:
    print("No valid trials for Exp1 (all dropped).")

# Exp1 plot: histogram of ratio_81
if HAS_MPL and len(df1) > 0:
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    ax.hist(df1["ratio_81"].clip(upper=df1["ratio_81"].quantile(0.99)), bins=50, edgecolor="k", alpha=0.7)
    ax.set_xlabel("ratio_81 (E_cl / (D_M · gap · K²))")
    ax.set_ylabel("Count")
    ax.set_title("Exp1 OP 8.1 ratio_81 (v004, random q_star)")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "exp1_ratio81_hist.png", dpi=120)
    plt.close(fig)
    print("Saved exp1_ratio81_hist.png")

# ── EXPERIMENT 2: Perturbation hazard (v004: perturb_str=0.32, max_steps=50) ──

print("\n" + "=" * 70)
print("EXPERIMENT 2: Assumption 6.3 — Perturbation Hazard (v004)")
print("=" * 70)

n2, N2 = 8, 500
collapse_thresh = 0.20
max_steps = 50   # v004: 40 → 50
perturb_str = 0.32   # v004: 0.28 → 0.32

t0 = time.time()
results_2 = []
# For survival: record E_trajectory per trial so we can compute frac surviving at each step by quartile
E_trajectories = []   # list of (E0_quartile_label, list of E at steps 0..max_steps)

for trial in range(N2):
    c_val = np.random.uniform(0.1, 5.0)
    K0 = random_kernel(n2, c=c_val)
    pi0 = stationary(K0)
    q0 = random_partition(n2, 2)
    Pi0 = L2_proj(q0, pi0, n2)
    E0 = closure_energy(K0, Pi0, pi0)
    g0 = abs_gap(K0, pi0)

    Kc = K0.copy()
    collapse_step = max_steps
    E_trajectory = [E0]

    for step in range(1, max_steps + 1):
        noise = random_kernel(n2, c=1.0)
        Kc = (1 - perturb_str) * Kc + perturb_str * noise
        Kc /= Kc.sum(axis=1, keepdims=True) + 1e-15
        pic = stationary(Kc)
        Pic = L2_proj(q0, pic, n2)
        Ec = closure_energy(Kc, Pic, pic)
        E_trajectory.append(Ec)
        if Ec > collapse_thresh:
            collapse_step = step
            break

    results_2.append({
        "trial": trial, "E0": E0, "g0": g0, "c_val": c_val,
        "collapse_step": collapse_step,
        "collapsed": collapse_step < max_steps,
        "E_final": E_trajectory[-1],
    })
    E_trajectories.append(E_trajectory)

df2 = pd.DataFrame(results_2)
df2["E0_quartile"] = pd.qcut(df2["E0"], 4, labels=["Q1 (low)", "Q2", "Q3", "Q4 (high)"], duplicates="drop")

# Survival table: at each step, fraction of trials (by quartile) that have not yet exceeded threshold
survival_rows = []
for step in range(max_steps + 1):
    row = {"step": step}
    for q in ["Q1 (low)", "Q2", "Q3", "Q4 (high)"]:
        mask = df2["E0_quartile"] == q
        if mask.sum() == 0:
            row[q] = np.nan
            continue
        # Survived at step = still have E <= threshold at this step (or not yet reached)
        survived = 0
        for i in df2.index[mask]:
            traj = E_trajectories[i]
            if step < len(traj) and traj[step] <= collapse_thresh:
                survived += 1
            # if step >= len(traj): collapsed earlier → not survived
        row[q] = survived / max(1, mask.sum())
    survival_rows.append(row)
df_survival = pd.DataFrame(survival_rows)
df_survival.to_csv(OUTPUT_DIR / "exp2_survival_by_quartile.csv", index=False)

grp2 = df2.groupby("E0_quartile", observed=True).agg(
    collapse_rate=("collapsed", "mean"),
    mean_steps=("collapse_step", "mean"),
    std_steps=("collapse_step", "std"),
    mean_E0=("E0", "mean"),
).reset_index()

corr_E0_steps = df2["E0"].corr(df2["collapse_step"])
path2 = OUTPUT_DIR / "exp2_hazard.csv"
df2.to_csv(path2, index=False)

print(f"Trials: {len(df2)}  |  Time: {time.time() - t0:.1f}s")
print("Collapse rate by E0 quartile:")
print(grp2.to_string(index=False))
print(f"\nCorrelation r(E0, collapse_step): {corr_E0_steps:.4f}")
print(f"collapse_step  std: {df2['collapse_step'].std():.2f}  25%/50%/75%: {df2['collapse_step'].quantile([0.25, 0.5, 0.75]).tolist()}")

# Exp2 plot: survival curves by quartile
if HAS_MPL:
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    for q in ["Q1 (low)", "Q2", "Q3", "Q4 (high)"]:
        if q in df_survival.columns:
            ax.plot(df_survival["step"], df_survival[q], label=q)
    ax.set_xlabel("Step")
    ax.set_ylabel("Fraction surviving (E ≤ threshold)")
    ax.set_title("Exp2 Survival by E0 quartile (v004)")
    ax.legend()
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "exp2_survival_curves.png", dpi=120)
    plt.close(fig)
    print("Saved exp2_survival_curves.png")

# ── EXPERIMENT 3: Skeleton + baselines with 3-step and multi-step baselines (v004) ──

print("\n" + "=" * 70)
print("EXPERIMENT 3: Coordination Skeleton (v004: 3-step + 2/3-step baselines)")
print("=" * 70)

n3, nag3, N3 = 8, 6, 500
MIS_S3 = 100
E_THRESHOLD = 0.01   # fraction of trials with E_final < this

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

    # Skeleton 1-step
    E_A1, Kn1 = align_measure(Ks, q, wi, wj)
    pin1 = stationary(np.mean(Kn1, axis=0))
    M2 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            mij = mis_sampled(pin1, n3, m=2, S=50)
            M2[i, j] = M2[j, i] = mij
    wi2, wj2 = np.unravel_index(np.triu(M2, 1).argmax(), M2.shape)
    E_A2, Kn2 = align_measure(Kn1, q, wi2, wj2)
    pin2 = stationary(np.mean(Kn2, axis=0))
    M3 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            mij = mis_sampled(pin2, n3, m=2, S=50)
            M3[i, j] = M3[j, i] = mij
    wi3, wj3 = np.unravel_index(np.triu(M3, 1).argmax(), M3.shape)
    E_A3, _ = align_measure(Kn2, q, wi3, wj3)

    # Random 1, 2, 3-step
    E_B1, Kn_r1 = align_measure(Ks, q, ri, rj)
    ri2, rj2 = pairs[np.random.randint(len(pairs))]
    E_B2, Kn_r2 = align_measure(Kn_r1, q, ri2, rj2)
    ri3, rj3 = pairs[np.random.randint(len(pairs))]
    E_B3, _ = align_measure(Kn_r2, q, ri3, rj3)

    # Centrality 1, 2, 3-step
    E_C1, Kn_c1 = align_measure(Ks, q, ci, cj)
    # Recompute centrality from Kn_c1
    pin_c1 = stationary(np.mean(Kn_c1, axis=0))
    Mc1 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            Mc1[i, j] = Mc1[j, i] = mis_sampled(pin_c1, n3, m=2, S=30)
    ci2 = int(np.argmax(Mc1.sum(axis=1)))
    row_c1 = Mc1[ci2].copy()
    row_c1[ci2] = -np.inf
    cj2 = int(np.argmax(row_c1))
    E_C2, Kn_c2 = align_measure(Kn_c1, q, ci2, cj2)
    pin_c2 = stationary(np.mean(Kn_c2, axis=0))
    Mc2 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            Mc2[i, j] = Mc2[j, i] = mis_sampled(pin_c2, n3, m=2, S=30)
    ci3 = int(np.argmax(Mc2.sum(axis=1)))
    row_c2 = Mc2[ci3].copy()
    row_c2[ci3] = -np.inf
    cj3 = int(np.argmax(row_c2))
    E_C3, _ = align_measure(Kn_c2, q, ci3, cj3)

    dE_skel_1 = E0 - E_A1
    dE_skel_2 = E0 - E_A2
    dE_skel_3 = E0 - E_A3
    dE_rand_1 = E0 - E_B1
    dE_rand_2 = E0 - E_B2
    dE_rand_3 = E0 - E_B3
    dE_cen_1 = E0 - E_C1
    dE_cen_2 = E0 - E_C2
    dE_cen_3 = E0 - E_C3

    all_dE = [dE_skel_1, dE_skel_2, dE_skel_3, dE_rand_1, dE_rand_2, dE_rand_3, dE_cen_1, dE_cen_2, dE_cen_3]
    best_dE = max(all_dE)
    skel_3step_best = best_dE == dE_skel_3

    results_3.append({
        "E0": E0,
        "dE_skeleton_1": dE_skel_1, "dE_skeleton_2": dE_skel_2, "dE_skeleton_3": dE_skel_3,
        "dE_random_1": dE_rand_1, "dE_random_2": dE_rand_2, "dE_random_3": dE_rand_3,
        "dE_centrality_1": dE_cen_1, "dE_centrality_2": dE_cen_2, "dE_centrality_3": dE_cen_3,
        "E_final_skel_1": E_A1, "E_final_skel_2": E_A2, "E_final_skel_3": E_A3,
        "E_final_random_1": E_B1, "E_final_random_2": E_B2, "E_final_random_3": E_B3,
        "E_final_centrality_1": E_C1, "E_final_centrality_2": E_C2, "E_final_centrality_3": E_C3,
        "skel_best": (dE_skel_1 > dE_rand_1 and dE_skel_1 > dE_cen_1),
        "skel_2step_best": (dE_skel_2 == best_dE),
        "skel_3step_best": skel_3step_best,
    })

df3 = pd.DataFrame(results_3)
path3 = OUTPUT_DIR / "exp3_skeleton.csv"
df3.to_csv(path3, index=False)

# Fraction E_final < E_THRESHOLD per strategy
print("\nFraction of trials with E_final < 0.01:")
for name, col in [
    ("Skeleton 1-step", "E_final_skel_1"), ("Skeleton 2-step", "E_final_skel_2"), ("Skeleton 3-step", "E_final_skel_3"),
    ("Random 1-step", "E_final_random_1"), ("Random 2-step", "E_final_random_2"), ("Random 3-step", "E_final_random_3"),
    ("Centrality 1-step", "E_final_centrality_1"), ("Centrality 2-step", "E_final_centrality_2"), ("Centrality 3-step", "E_final_centrality_3"),
]:
    frac = (df3[col] < E_THRESHOLD).mean()
    print(f"  {name}: {frac:.3f}")

print(f"\nTrials: {len(df3)}  |  Time: {time.time() - t0:.1f}s")
print("\nMean ΔE_cl reduction (positive = more reduction):")
print(f"  Skeleton 1/2/3-step : {df3.dE_skeleton_1.mean():.6f}  {df3.dE_skeleton_2.mean():.6f}  {df3.dE_skeleton_3.mean():.6f}")
print(f"  Random 1/2/3-step    : {df3.dE_random_1.mean():.6f}  {df3.dE_random_2.mean():.6f}  {df3.dE_random_3.mean():.6f}")
print(f"  Centrality 1/2/3-step: {df3.dE_centrality_1.mean():.6f}  {df3.dE_centrality_2.mean():.6f}  {df3.dE_centrality_3.mean():.6f}")
print("\nWin rates (best overall = max dE among all 9):")
print(f"  Skeleton 1-step best : {df3.skel_best.mean():.3f}")
print(f"  Skeleton 2-step best : {df3.skel_2step_best.mean():.3f}")
print(f"  Skeleton 3-step best : {df3.skel_3step_best.mean():.3f}")

# Exp3 boxplot data + figure
box_rows = []
for _, r in df3.iterrows():
    for lab, col in [
        ("Skel 1", "dE_skeleton_1"), ("Skel 2", "dE_skeleton_2"), ("Skel 3", "dE_skeleton_3"),
        ("Rand 1", "dE_random_1"), ("Rand 2", "dE_random_2"), ("Rand 3", "dE_random_3"),
        ("Cen 1", "dE_centrality_1"), ("Cen 2", "dE_centrality_2"), ("Cen 3", "dE_centrality_3"),
    ]:
        box_rows.append({"strategy": lab, "dE": r[col]})
box_df = pd.DataFrame(box_rows)
box_df.to_csv(OUTPUT_DIR / "exp3_boxplot_data.csv", index=False)

if HAS_MPL:
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    order = ["Skel 1", "Skel 2", "Skel 3", "Rand 1", "Rand 2", "Rand 3", "Cen 1", "Cen 2", "Cen 3"]
    data = [box_df.loc[box_df["strategy"] == s, "dE"].values for s in order]
    ax.boxplot(data, labels=order, patch_artist=True)
    ax.set_ylabel("ΔE_cl (E0 - E_final)")
    ax.set_title("Exp3 ΔE_cl by strategy (v004)")
    plt.xticks(rotation=25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "exp3_boxplot_dE.png", dpi=120)
    plt.close(fig)
    print("Saved exp3_boxplot_dE.png")

# ── Run summary ──

total_elapsed = time.time() - t_run_start
run_summary = {
    "run_id": RUN_ID,
    "script": "v3test_v004.py",
    "exp1": {"N1": N1, "n": n, "q_star": "random_partition(n, m=3)", "retained": len(df1), "drop_reasons": drop_reasons},
    "exp2": {"N2": N2, "perturb_str": perturb_str, "max_steps": max_steps, "collapse_thresh": collapse_thresh, "collapse_rate": float(df2["collapsed"].mean())},
    "exp3": {"N3": N3, "n3": n3, "nag3": nag3, "skel_3step_best_rate": float(df3.skel_3step_best.mean()), "skel_2step_best_rate": float(df3.skel_2step_best.mean()), "skel_best_rate": float(df3.skel_best.mean())},
    "output_dir": str(OUTPUT_DIR),
    "total_elapsed_sec": round(total_elapsed, 1),
}
(OUTPUT_DIR / "run_summary.json").write_text(json.dumps(run_summary, indent=2))
print("\nRun summary written to", OUTPUT_DIR / "run_summary.json")
print("Outputs:", sorted([p.name for p in OUTPUT_DIR.iterdir()]))
