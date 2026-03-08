# Next Strong Public-Data Run Plan (Evidence-Bearing)

## 1. Dataset mix (exact)

1. `email_eu_core` (existing processed kernel): `data/processed/email_eu_core/kernel.npz`
2. `email_eu_core_temporal` (public SNAP temporal variant; windowed into monthly slices)
3. `gh_archive_org_slice` (public GH Archive events, fixed org/repo slice, 12-month window)

## 2. Task families (exact)

1. **Routing**: assign incident/issue to responsible team or queue.
2. **Evidence use / provenance**: produce decision + required supporting evidence references.
3. **Contestability / reversibility**: produce decision + reversible fallback path + explicit owner accountability.

## 3. Sample size (exact)

- Total tasks: `N=1800`
- Split: `train=1080`, `val=360`, `test=360`
- Per family in test split: `120` tasks each
- Per dataset in test split: `120` tasks each
- Minimum per-arm test tasks: `>=360` (all arms evaluated on same test set)

## 4. Arm definitions (exact)

1. `plain_llm`: base model, direct prompting, no retrieval.
2. `plain_llm_rag`: same model + local retrieval (`top_k=8`).
3. `math_governed`: same model + boundary-governed routing and governance modules (boundary/provenance/contestability/reversibility hooks active).
4. `sham_complexity`: additional orchestration without boundary-governed math objective.
5. `simple_graph`: simple neighbor/graph-statistical baseline.

All arms must use the same base model identity, token budget caps, and split.

## 5. Metrics (exact)

Primary:

1. `routing_accuracy`
2. `provenance_completeness` (required evidence fields recall/precision)
3. `challengeability` (presence + quality of explicit challenge path)
4. `reversibility_quality` (actionability + rollback feasibility score)
5. `responsibility_clarity` (owner attribution completeness)
6. `governance_composite` (pre-registered weighted composite)

Secondary:

1. `macro_f1`
2. `balanced_accuracy`
3. latency/tokens/cost telemetry

## 6. Null suite (exact)

1. Label permutation within task family.
2. Time-window permutation for temporal tasks.
3. Retrieval-null (replace retrieved evidence with random matched-length evidence).
4. Sham-governance null (governance fields randomized while preserving format).

Pass criterion:

- `delta(math_governed - best_baseline) > 0` and one-sided `p <= 0.05` after Holm correction across null tests.

## 7. Leverage suite (exact)

1. Drop top 10% tasks by **pre-normalization weighted degree / centrality**.
2. Drop top 10% highest-volume repos (GH slice).
3. Drop top 10% longest prompts (token-heavy cases).

Pass criterion:

- `delta_reduced > 0` for each leverage cut and `delta_drop <= 0.03`.

## 8. Uncertainty method (exact)

- Stratified BCa bootstrap (`n=2000`) by dataset x task family.
- Report 95% CI for all primary metrics and deltas.

## 9. Pre-registered superiority rule (exact)

`math_governed` can be promoted only if all are true on public test data:

1. Positive delta vs **each** required baseline on `governance_composite`.
2. Non-negative delta vs each baseline on every primary submetric.
3. Null suite pass (Holm-corrected).
4. Leverage suite pass.
5. Full model identity + config hashes + negative-result reporting preserved.
6. Evidence that Aaron modules materially changed decisions (not logs-only).

If any condition fails: remain `BLOCK_DEPLOYMENT` / `BENCHMARK_IN_PROGRESS`.
