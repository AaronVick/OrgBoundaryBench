# Temporal Drift Completion Report

## Corpus 1: email-Eu-core-temporal
- status: completed
- processed windows: 8 (max_nodes=30)
- PRD-30 temporal subtest: PASS

## Corpus 2: wiki-talk-temporal
- status: completed (feasible public slice)
- processed windows: 8 (max_nodes=30, max_edges=1,500,000)
- PRD-30 temporal subtest: PASS

## Updated temporal report (primary run)
- `outputs/temporal_drift_report.md` refreshed from temporal-enabled PRD-30 run.

### email temporal report excerpt:
# Temporal Drift Report

- status: `run`
- pass: `True`
- phase_alert_steps: `[]`
- baseline_alerts: `{'density_drift': [3], 'entropy_drift': [2], 'spectral_gap_drift': [7]}`
- median_lead_time_phase: `0.0`
- fp_rate_phase: `0.0`

### wiki temporal report excerpt:
# Temporal Drift Report

- status: `run`
- pass: `True`
- phase_alert_steps: `[]`
- baseline_alerts: `{'density_drift': [2], 'entropy_drift': [2], 'spectral_gap_drift': [7]}`
- median_lead_time_phase: `0.0`
- fp_rate_phase: `0.0`
