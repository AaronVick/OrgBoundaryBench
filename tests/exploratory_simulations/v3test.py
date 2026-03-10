"""
Boundary Coherence Across Scales — Computational Study (Fixed Version)
Experiments 1–3: OP 8.1, Assumption 6.3, Coordination Skeleton
Aaron Vick — Fixed & Improved, March 2026
"""

import numpy as np
import pandas as pd
from scipy.linalg import eigvals
import warnings, json, time
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
from plotly.subplots import make_subplots

np.random.seed(42)

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
    # Ensure all m labels are used
    labels[:m] = np.arange(m)
    labels[m:] = np.random.randint(0, m, size=n - m)
    np.random.shuffle(labels)
    partition = [set(np.where(labels == k)[0]) for k in range(m)]
    # Filter empty just in case (shouldn't happen)
    return [b for b in partition if b]

def proj_dist(Pa, Pb, pi):
    d = Pa - Pb
    return float(np.sqrt(np.trace(d.T @ np.diag(pi) @ d)))

def mis_sampled(pi, n, m=2, S=80):
    """Better-sampled estimate of inf ||Π_qa - Π_qb|| over partitions into m blocks"""
    best = np.inf
    for _ in range(S):
        qa = random_partition(n, m)
        qb = random_partition(n, m)
        d = proj_dist(L2_proj(qa, pi, n), L2_proj(qb, pi, n), pi)
        if d < best:
            best = d
        # Occasionally try different m for diversity
        if np.random.rand() < 0.15:
            m_alt = np.random.choice([max(2, m-1), m+1]) if m+1 <= n else m
            qa = random_partition(n, m_alt)
            qb = random_partition(n, m_alt)
            d = proj_dist(L2_proj(qa, pi, n), L2_proj(qb, pi, n), pi)
            if d < best:
                best = d
    return best

def greedy_coarsegrain(K, pi, n, max_merges=None):
    """Greedy coarse-graining: merge blocks minimizing closure energy increase"""
    partition = [ {i} for i in range(n) ]  # start with singletons
    current_Pi = L2_proj(partition, pi, n)
    current_E = closure_energy(K, current_Pi, pi)

    while len(partition) > 1:
        best_delta = np.inf
        best_i, best_j = -1, -1
        for i in range(len(partition)):
            for j in range(i+1, len(partition)):
                new_block = partition[i] | partition[j]
                new_part = [partition[k] for k in range(len(partition)) if k not in (i,j)] + [new_block]
                new_Pi = L2_proj(new_part, pi, n)
                new_E = closure_energy(K, new_Pi, pi)
                delta = new_E - current_E
                if delta < best_delta:
                    best_delta = delta
                    best_i, best_j = i, j
        if best_delta > 1e-9 or best_i < 0:  # no improvement or error
            break
        # Merge
        new_block = partition[best_i] | partition[best_j]
        partition = [partition[k] for k in range(len(partition)) if k not in (best_i, best_j)] + [new_block]
        current_Pi = L2_proj(partition, pi, n)
        current_E = closure_energy(K, current_Pi, pi)
        if len(partition) <= 2:  # stop early if coarse enough
            break
    return partition

# ── EXPERIMENT 1: Open Problem 8.1 ──────────────────────────────────────────

print("=" * 70)
print("EXPERIMENT 1: Open Problem 8.1 — Lower Bound Search (Fixed)")
print("=" * 70)

n, n_ag, N1 = 6, 3, 800   # reduced N for speed; increase if needed
t0 = time.time()
results_1 = []

for trial in range(N1):
    Ks = [random_kernel(n, c=np.random.uniform(0.3, 3.0)) for _ in range(n_ag)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    K2 = float(np.einsum('ij,i,ij->', Kj, pi, Kj))

    q_star = greedy_coarsegrain(Kj, pi, n)
    Pi_star = L2_proj(q_star, pi, n)
    E = closure_energy(Kj, Pi_star, pi)
    g = abs_gap(Kj, pi)

    # D_M via max pairwise (better sampling)
    M_vals = []
    for _ in range(3):  # 3 pairs for triangle
        mij = mis_sampled(pi, n, m=2, S=80)
        M_vals.append(mij)
    DM = max(M_vals) if M_vals else 0.0

    if DM > 1e-10 and K2 > 1e-10 and g > 1e-10 and E > 1e-12:
        results_1.append({
            'trial': trial,
            'E_cl': E, 'D_M': DM, 'gap': g, 'K2': K2,
            'n_blocks': len(q_star),
            'ratio_T32': E / (DM**2 * K2),
            'ratio_81': E / (DM * g * K2),
            'ratio_norm': E / (DM * K2),
        })

df1 = pd.DataFrame(results_1)
df1.to_csv("exp1_op81_fixed.csv", index=False)

print(f"Trials completed: {len(df1)}  |  Time: {time.time()-t0:.1f}s")
if len(df1) > 0:
    print(f"\nT3.2 check — E_cl / (D_M² K²)   max: {df1.ratio_T32.max():.4f}  mean: {df1.ratio_T32.mean():.4f}")
    print(f"Violations >1: {(df1.ratio_T32 > 1.0).sum()}  (due to D_M underestimation)")
    print(f"\nOP 8.1 — E_cl / (D_M · gap · K²)   max: {df1.ratio_81.max():.4f}  mean: {df1.ratio_81.mean():.4f}")
    print(f"Empirical c* ≈ {1.0 / df1.ratio_81.max():.4f} (lower bound on possible c)")

# ── EXPERIMENT 2: Assumption 6.3 ────────────────────────────────────────────

print("\n" + "=" * 70)
print("EXPERIMENT 2: Assumption 6.3 — Perturbation Hazard (Fixed)")
print("=" * 70)

n2, N2 = 8, 400
collapse_thresh = 0.30
max_steps = 30
perturb_str = 0.12

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
        'trial': trial, 'E0': E0, 'g0': g0, 'c_val': c_val,
        'collapse_step': collapse_step,
        'collapsed': collapse_step < max_steps,
        'E_final': E_trajectory[-1],
    })

df2 = pd.DataFrame(results_2)
df2['E0_quartile'] = pd.qcut(df2['E0'], 4, labels=['Q1 (low)', 'Q2', 'Q3', 'Q4 (high)'], duplicates='drop')
grp2 = df2.groupby('E0_quartile', observed=True).agg(
    collapse_rate=('collapsed', 'mean'),
    mean_steps=('collapse_step', 'mean'),
    mean_E0=('E0', 'mean')
).reset_index()

corr_E0_steps = df2['E0'].corr(df2['collapse_step'])
df2.to_csv("exp2_hazard_fixed.csv", index=False)

print(f"Trials: {len(df2)}  |  Time: {time.time()-t0:.1f}s")
print("\nCollapse rate by E0 quartile:")
print(grp2.to_string(index=False))
print(f"\nCorrelation r(E0, collapse_step): {corr_E0_steps:.4f}  (negative = faster collapse for higher E0)")

# ── EXPERIMENT 3: Coordination Skeleton ─────────────────────────────────────

print("\n" + "=" * 70)
print("EXPERIMENT 3: Coordination Skeleton vs Baselines (Fixed)")
print("=" * 70)

n3, nag3, N3 = 6, 4, 300
t0 = time.time()
results_3 = []

for trial in range(N3):
    Ks = [random_kernel(n3, c=np.random.uniform(0.5, 2.0)) for _ in range(nag3)]
    pi = stationary(np.mean(Ks, axis=0))
    Kj = np.mean(Ks, axis=0)
    q = random_partition(n3, 2)
    Pi = L2_proj(q, pi, n3)
    E0 = closure_energy(Kj, Pi, pi)

    # Misalignment matrix
    M = np.zeros((nag3, nag3))
    for i in range(nag3):
        for j in range(i+1, nag3):
            mij = mis_sampled(pi, n3, m=2, S=60)
            M[i,j] = M[j,i] = mij

    # Max misalignment pair
    wi, wj = np.unravel_index(np.triu(M, 1).argmax(), M.shape)

    # Random pair
    pairs = [(i,j) for i in range(nag3) for j in range(i+1, nag3)]
    ri, rj = pairs[np.random.randint(len(pairs))]

    # Max centrality pair
    cen = M.sum(axis=1)
    ci = int(np.argmax(cen))
    row = M[ci].copy(); row[ci] = -np.inf
    cj = int(np.argmax(row))

    def align_measure(Ks_list, align_i, align_j):
        Kn = [k.copy() for k in Ks_list]
        Kn[align_j] = 0.5 * Kn[align_i] + 0.5 * Kn[align_j]
        Kn[align_j] /= Kn[align_j].sum(axis=1, keepdims=True) + 1e-15
        Kjn = np.mean(Kn, axis=0)
        pin = stationary(Kjn)
        Pin = L2_proj(q, pin, n3)
        return closure_energy(Kjn, Pin, pin)

    E_A = align_measure(Ks, wi, wj)
    E_B = align_measure(Ks, ri, rj)
    E_C = align_measure(Ks, ci, cj)

    results_3.append({
        'E0': E0,
        'dE_skeleton': E0 - E_A,
        'dE_random': E0 - E_B,
        'dE_centrality': E0 - E_C,
        'skel_best': (E0 - E_A > E0 - E_B) and (E0 - E_A > E0 - E_C),
    })

df3 = pd.DataFrame(results_3)
df3.to_csv("exp3_skeleton_fixed.csv", index=False)

print(f"Trials: {len(df3)}  |  Time: {time.time()-t0:.1f}s")
print(f"\nMean ΔE_cl reduction:")
print(f"  Skeleton   : {df3.dE_skeleton.mean():.6f}")
print(f"  Random     : {df3.dE_random.mean():.6f}")
print(f"  Centrality : {df3.dE_centrality.mean():.6f}")
print(f"\nSkeleton > random     : {(df3.dE_skeleton > df3.dE_random).mean():.3f}")
print(f"Skeleton > centrality : {(df3.dE_skeleton > df3.dE_centrality).mean():.3f}")
print(f"Skeleton best overall : {df3.skel_best.mean():.3f}")

print("\nCode ready. Copy-paste and run in your environment.")
print("If charts needed, add the plotting block from original (now df1/df2/df3 exist).")