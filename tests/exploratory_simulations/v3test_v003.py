"""
Boundary Coherence Across Scales — Computational Study v003
Experiments 1–3: OP 8.1, Assumption 6.3, Coordination Skeleton

Version: 003
Run ID: run003
Base: v3test_v002.py. Changes driven by findings_run001.md, findings_run002.md.

CHANGELOG v002 → v003:
  Exp1: D_M now max(mis_sampled, fixed_coarse_diameter) so denominator is non-trivial;
        fixed_coarse_diameter = max pairwise proj_dist over 3 canonical 2-block splits.
        DM_MIN relaxed to 1e-14; n=10 (was 6) for larger partition scale; N1=2000.
  Exp2: perturb_str 0.20→0.28, collapse_thresh 0.30→0.20; N2=500.
  Exp3: Two-step skeleton alignment added; report dE_skeleton_1, dE_skeleton_2, dE_random,
        dE_centrality; skel_best (1-step), skel_2step_best; quantiles for all strategies.
  All outputs to docs/exploratory_simulations/run003/.
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
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

RUN_ID = "003"
OUTPUT_DIR = Path(__file__).resolve().parent / "run003"
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
    """v003: Max pairwise L2 projection distance over canonical 2-block splits.
    Ensures D_M has positive scale when mis_sampled infimum is tiny."""
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


def greedy_coarsegrain(K, pi, n, max_merges=None):
    """Greedy coarse-graining: merge blocks minimizing closure energy increase"""
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


# ── EXPERIMENT 1: Open Problem 8.1 (v003: D_M = max(mis_sampled, fixed_coarse_diameter), n=10) ──

print("=" * 70)
print("EXPERIMENT 1: Open Problem 8.1 — Lower Bound Search (v003)")
print("=" * 70)

DM_MIN, K2_MIN, G_MIN, E_MIN = 1e-14, 1e-12, 1e-12, 1e-14
n, n_ag, N1 = 10, 3, 2000   # v003: n 6→10 for larger partition scale
MIS_SAMPLES = 200

t0 = time.time()
results_1 = []
drop_reasons = {"DM": 0, "K2": 0, "gap": 0, "E": 0, "ok": 0}

for trial in range(N1):
    Ks = [random_kernel(n, c=np.random.uniform(0.3, 3.0)) for _ in range(n_ag)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    K2 = float(np.einsum("ij,i,ij->", Kj, pi, Kj))

    q_star = greedy_coarsegrain(Kj, pi, n)
    Pi_star = L2_proj(q_star, pi, n)
    E = closure_energy(Kj, Pi_star, pi)
    g = abs_gap(Kj, pi)

    # v003: D_M = max(infimum estimate, fixed coarse diameter) so denominator is non-trivial
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
    print(f"D_M stats: mean={df1['D_M'].mean():.6f}  fixed component mean={df1['D_M_fixed'].mean():.6f}")
else:
    print("No valid trials for Exp1 (all dropped).")

# ── EXPERIMENT 2: Assumption 6.3 (v003: perturb_str=0.28, collapse_thresh=0.20) ──

print("\n" + "=" * 70)
print("EXPERIMENT 2: Assumption 6.3 — Perturbation Hazard (v003)")
print("=" * 70)

n2, N2 = 8, 500   # v003: N2 400→500
collapse_thresh = 0.20   # v003: 0.30 → 0.20
max_steps = 40
perturb_str = 0.28   # v003: 0.20 → 0.28

t0 = time.time()
results_2 = []

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

df2 = pd.DataFrame(results_2)
df2["E0_quartile"] = pd.qcut(df2["E0"], 4, labels=["Q1 (low)", "Q2", "Q3", "Q4 (high)"], duplicates="drop")
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

# ── EXPERIMENT 3: Coordination Skeleton (v003: two-step skeleton + full quantiles) ──

print("\n" + "=" * 70)
print("EXPERIMENT 3: Coordination Skeleton vs Baselines (v003, incl. 2-step skeleton)")
print("=" * 70)

n3, nag3, N3 = 8, 6, 500
MIS_S3 = 100

t0 = time.time()
results_3 = []

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

    def align_measure(Ks_list, part, align_i, align_j):
        Kn = [k.copy() for k in Ks_list]
        Kn[align_j] = 0.5 * Kn[align_i] + 0.5 * Kn[align_j]
        Kn[align_j] /= Kn[align_j].sum(axis=1, keepdims=True) + 1e-15
        Kjn = np.mean(Kn, axis=0)
        pin = stationary(Kjn)
        Pin = L2_proj(part, pin, n3)
        return closure_energy(Kjn, Pin, pin), Kn

    # 1-step
    E_A1, Kn1 = align_measure(Ks, q, wi, wj)
    E_B = align_measure(Ks, q, ri, rj)[0]
    E_C = align_measure(Ks, q, ci, cj)[0]

    # v003: 2-step skeleton — from Kn1, recompute M and align next max-misalignment pair
    pin1 = stationary(np.mean(Kn1, axis=0))
    M2 = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i + 1, nag3):
            mij = mis_sampled(pin1, n3, m=2, S=50)
            M2[i, j] = M2[j, i] = mij
    wi2, wj2 = np.unravel_index(np.triu(M2, 1).argmax(), M2.shape)
    E_A2, _ = align_measure(Kn1, q, wi2, wj2)

    dE_skel_1 = E0 - E_A1
    dE_skel_2 = E0 - E_A2

    results_3.append({
        "E0": E0,
        "dE_skeleton_1": dE_skel_1,
        "dE_skeleton_2": dE_skel_2,
        "dE_random": E0 - E_B,
        "dE_centrality": E0 - E_C,
        "skel_best": (dE_skel_1 > E0 - E_B) and (dE_skel_1 > E0 - E_C),
        "skel_2step_best": (dE_skel_2 > E0 - E_B) and (dE_skel_2 > E0 - E_C),
    })

df3 = pd.DataFrame(results_3)
path3 = OUTPUT_DIR / "exp3_skeleton.csv"
df3.to_csv(path3, index=False)

print(f"Trials: {len(df3)}  |  Time: {time.time() - t0:.1f}s")
print("\nMean ΔE_cl reduction (positive = more reduction):")
print(f"  Skeleton 1-step : {df3.dE_skeleton_1.mean():.6f}  std: {df3.dE_skeleton_1.std():.6f}")
print(f"  Skeleton 2-step : {df3.dE_skeleton_2.mean():.6f}  std: {df3.dE_skeleton_2.std():.6f}")
print(f"  Random          : {df3.dE_random.mean():.6f}  std: {df3.dE_random.std():.6f}")
print(f"  Centrality      : {df3.dE_centrality.mean():.6f}  std: {df3.dE_centrality.std():.6f}")
print("\nQuantiles (0.25, 0.5, 0.75):")
print("  dE_skeleton_1:", df3.dE_skeleton_1.quantile([0.25, 0.5, 0.75]).round(6).tolist())
print("  dE_skeleton_2:", df3.dE_skeleton_2.quantile([0.25, 0.5, 0.75]).round(6).tolist())
print("  dE_random:    ", df3.dE_random.quantile([0.25, 0.5, 0.75]).round(6).tolist())
print("  dE_centrality:", df3.dE_centrality.quantile([0.25, 0.5, 0.75]).round(6).tolist())
print("\nWin rates:")
print(f"  Skeleton 1-step best overall : {df3.skel_best.mean():.3f}")
print(f"  Skeleton 2-step best overall: {df3.skel_2step_best.mean():.3f}")
print(f"  Skeleton 1-step > random    : {(df3.dE_skeleton_1 > df3.dE_random).mean():.3f}")
print(f"  Skeleton 1-step > centrality: {(df3.dE_skeleton_1 > df3.dE_centrality).mean():.3f}")
print(f"  Skeleton 2-step > random    : {(df3.dE_skeleton_2 > df3.dE_random).mean():.3f}")
print(f"  Skeleton 2-step > centrality : {(df3.dE_skeleton_2 > df3.dE_centrality).mean():.3f}")

# ── Run summary for findings doc ──

total_elapsed = time.time() - t_run_start
run_summary = {
    "run_id": RUN_ID,
    "script": "v3test_v003.py",
    "exp1": {"N1": N1, "n": n, "retained": len(df1), "drop_reasons": drop_reasons},
    "exp2": {"N2": N2, "perturb_str": perturb_str, "max_steps": max_steps, "collapse_thresh": collapse_thresh, "collapse_rate": float(df2["collapsed"].mean())},
    "exp3": {"N3": N3, "n3": n3, "nag3": nag3, "skel_best_rate": float(df3.skel_best.mean()), "skel_2step_best_rate": float(df3.skel_2step_best.mean())},
    "output_dir": str(OUTPUT_DIR),
    "total_elapsed_sec": round(total_elapsed, 1),
}
(OUTPUT_DIR / "run_summary.json").write_text(json.dumps(run_summary, indent=2))
print("\nRun summary written to", OUTPUT_DIR / "run_summary.json")
print("Outputs:", list(OUTPUT_DIR.iterdir()))
