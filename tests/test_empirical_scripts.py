"""
Integration tests: each empirical run script (PRD-17–22) is executed and expected outputs verified.

PhD rigor: testing frameworks are not only unit-tested but end-to-end tested — the documented
entry points must produce the documented outputs. Methodology: outputs/METHODOLOGY.md §6.2.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_script(script_name: str, args: list[str], out_dir: Path) -> subprocess.CompletedProcess:
    """Run script with --out-dir; return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name), "--out-dir", str(out_dir)] + args,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_run_boundary_benchmark_script(tmp_path: Path) -> None:
    """PRD-17: run_boundary_benchmark.py produces boundary_benchmark_report.txt with leaderboard and success."""
    r = _run_script("run_boundary_benchmark.py", ["--n", "8", "--n-random", "1"], tmp_path)
    assert r.returncode in (0, 1), f"Script failed: {r.stderr}"
    report = tmp_path / "boundary_benchmark_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Leaderboard" in text or "leaderboard" in text.lower()
    assert "Success" in text or "success" in text.lower()
    assert "q_star" in text or "one_block" in text


def test_run_governance_stress_script(tmp_path: Path) -> None:
    """PRD-18: run_governance_stress.py produces governance_stress_report.txt with summary and pass."""
    r = _run_script("run_governance_stress.py", ["--n", "8"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "governance_stress_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Summary" in text or "mean_nmi" in text
    assert "pass" in text.lower()
    assert "noise" in text or "missingness" in text


def test_run_quiet_error_lab_script(tmp_path: Path) -> None:
    """PRD-19: run_quiet_error_lab.py produces quiet_error_report.txt with detection and pass."""
    r = _run_script("run_quiet_error_lab.py", ["--n", "6", "--n-planted", "2", "--n-control", "2"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "quiet_error_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "detection_rate" in text
    assert "false_reassurance" in text or "false_reassurance_rate" in text
    assert "pass" in text.lower()


def test_run_misalignment_engine_script(tmp_path: Path) -> None:
    """PRD-20: run_misalignment_engine.py produces misalignment_report.txt with m_n and pass."""
    r = _run_script("run_misalignment_engine.py", ["--n", "8"], tmp_path)
    assert r.returncode == 0
    report = tmp_path / "misalignment_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "m_n" in text
    assert "n_blocks_pred" in text
    assert "pass" in text.lower()


def test_run_rcti_comparative_script(tmp_path: Path) -> None:
    """PRD-21: run_rcti_comparative.py produces rcti_comparative_report.txt with constructions and baselines."""
    r = _run_script("run_rcti_comparative.py", ["--n", "6", "--no-gudhi"], tmp_path)
    assert r.returncode == 0
    report = tmp_path / "rcti_comparative_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Construction" in text or "construction" in text.lower()
    assert "C1" in text or "C4b" in text
    assert "density" in text or "Baselines" in text


def test_run_phase_monitoring_script(tmp_path: Path) -> None:
    """PRD-22: run_phase_monitoring.py produces phase_monitoring_report.txt with trajectory and flags."""
    r = _run_script("run_phase_monitoring.py", ["--n", "6", "--n-steps", "3"], tmp_path)
    assert r.returncode == 0
    report = tmp_path / "phase_monitoring_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Trajectory" in text or "trajectory" in text.lower()
    assert "step" in text
    assert "E_cl" in text or "n_blocks" in text
    assert "Flags" in text or "flags" in text.lower()


def test_run_null_rival_audit_script(tmp_path: Path) -> None:
    """PRD II (thoughts3): run_null_rival_audit.py produces null_rival_audit_report.txt."""
    r = _run_script("run_null_rival_audit.py", ["--n", "8"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "null_rival_audit_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "D" in text and "Pass" in text


def test_run_leverage_stability_script(tmp_path: Path) -> None:
    """PRD III (thoughts3): run_leverage_stability.py produces leverage_stability_report.txt."""
    r = _run_script("run_leverage_stability.py", ["--n", "8", "--n-trials", "1"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "leverage_stability_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "S_max" in text and "Pass" in text


def test_run_misalignment_outcome_validation_script(tmp_path: Path) -> None:
    """PRD-26: run_misalignment_outcome_validation.py produces misalignment_outcome_report.txt."""
    r = _run_script("run_misalignment_outcome_validation.py", ["--n-units", "6", "--n-nodes", "4"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "misalignment_outcome_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "corr" in text or "Correlations" in text
    assert "pass" in text.lower()


def test_run_cross_construction_invariance_script(tmp_path: Path) -> None:
    """PRD-28: run_cross_construction_invariance.py produces cross_construction_invariance_report.txt."""
    r = _run_script("run_cross_construction_invariance.py", ["--n-samples", "4", "--n", "5", "--no-gudhi"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "cross_construction_invariance_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "construction" in text.lower()
    assert "pass" in text.lower()


def test_run_incident_phase_monitoring_script(tmp_path: Path) -> None:
    """PRD-24: run_incident_phase_monitoring.py produces incident_phase_report.txt with lead time and pass."""
    r = _run_script("run_incident_phase_monitoring.py", ["--n-steps", "5", "--incident-at", "3"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "incident_phase_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "lead time" in text.lower() or "Phase" in text
    assert "pass" in text.lower()
    assert "Baseline" in text or "baseline" in text


def test_run_governance_metrics_script(tmp_path: Path) -> None:
    """PRD-25: run_governance_metrics.py produces governance_metrics_report.txt with reversal success and pass."""
    r = _run_script("run_governance_metrics.py", ["--n", "5"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "governance_metrics_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Reversal success" in text
    assert "Override latency" in text or "override" in text.lower()
    assert "pass" in text.lower()


def test_run_rcti_sedation_test_script(tmp_path: Path) -> None:
    """PRD-27: run_rcti_sedation_test.py produces rcti_sedation_report.txt with AUC and pass."""
    r = _run_script("run_rcti_sedation_test.py", ["--n", "5", "--n-per-class", "2", "--no-gudhi"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "rcti_sedation_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "AUC" in text
    assert "Pass" in text or "pass" in text.lower()
    assert "Construction" in text or "construction" in text.lower()


def test_run_nontrivial_boundary_public_script(tmp_path: Path) -> None:
    """PRD-23: run_nontrivial_boundary_public.py produces nontrivial_boundary_report.txt with leaderboard and agreement."""
    r = _run_script("run_nontrivial_boundary_public.py", ["--n", "8", "--n-random", "2"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "nontrivial_boundary_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Leaderboard" in text or "leaderboard" in text.lower()
    assert "External agreement" in text or "NMI" in text
    assert "Meaningful" in text or "Useless" in text or "meaningful" in text.lower()
    assert "q_star" in text or "one_block" in text


def test_run_cross_modal_replication_script(tmp_path: Path) -> None:
    """PRD VIII (thoughts3): run_cross_modal_replication.py produces cross_modal_replication_report.txt."""
    r = _run_script("run_cross_modal_replication.py", ["--n", "5", "--n-per-class", "2", "--no-gudhi"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "cross_modal_replication_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "direction" in text.lower() or "delta_T" in text
    assert "Pass" in text


def test_run_confirmation_bias_stress_script(tmp_path: Path) -> None:
    """PRD X (thoughts3): run_confirmation_bias_stress.py produces confirmation_bias_stress_report.txt."""
    r = _run_script("run_confirmation_bias_stress.py", ["--n", "8", "--n-visible", "2", "--n-quiet", "2", "--n-control", "2"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "confirmation_bias_stress_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "challenge" in text.lower()
    assert "Pass" in text or "rubber" in text.lower()


def test_run_extended_rigor_script(tmp_path: Path) -> None:
    """PRD-11: run_extended_rigor.py produces extended_rigor_report.txt with Replication, Sensitivity, checklist."""
    r = _run_script("run_extended_rigor.py", ["--n", "8", "--n-seeds", "2", "--n-values", "6", "8"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "extended_rigor_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Replication" in text and "Sensitivity" in text
    assert "checklist" in text.lower() and "Pass" in text


def test_run_adversarial_audit_script(tmp_path: Path) -> None:
    """PRD-16: run_adversarial_audit.py produces adversarial_audit_report.txt with Q1–Q4 checklist."""
    r = _run_script("run_adversarial_audit.py", ["--n", "8"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "adversarial_audit_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Adversarial" in text and "Q1" in text
    assert "Q2" in text and "Pass" in text


def test_run_usecase_ii_audit_script(tmp_path: Path) -> None:
    """Usecase PRD II (useccases.md): run_usecase_ii_audit.py produces usecase_II_report.txt with scientific-method sections."""
    r = _run_script("run_usecase_ii_audit.py", ["--n", "8", "--n-trials", "1"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "usecase_II_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Hypothesis" in text and "Methods" in text
    assert "Public data used" in text and "Baseline" in text
    assert "Outcomes" in text and "Falsification" in text
    assert "What would make this look good" in text
    assert "Pass" in text and "D" in text and "S_max" in text


def test_run_email_eu_core_usecase_ii_script(tmp_path: Path) -> None:
    """Deliverable 1 (organizational_empirical_validation.md): run_email_eu_core_usecase_ii.py produces report and outcomes summary when data present."""
    data_npz = ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz"
    if not data_npz.exists():
        pytest.skip("email_eu_core data not present (run download_and_normalize.py --source email_eu_core)")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_email_eu_core_usecase_ii.py"), "--out-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode in (0, 1), f"Script failed: {r.stderr}"
    report = tmp_path / "usecase_II_report.txt"
    summary = tmp_path / "outcomes_summary.yaml"
    assert report.exists(), f"Expected report: {report}"
    assert summary.exists(), f"Expected summary: {summary}"
    text = report.read_text()
    assert "Public data used" in text and "Outcomes" in text and "mean_D" in text and "S_max" in text
    yaml_text = summary.read_text()
    assert "mean_D" in yaml_text and "data_source" in yaml_text


def test_run_usecase_iii_drift_benchmark_script(tmp_path: Path) -> None:
    """Usecase PRD III (useccases.md): run_usecase_iii_drift_benchmark.py produces usecase_III_report.txt with scientific-method sections."""
    r = _run_script("run_usecase_iii_drift_benchmark.py", ["--n-steps", "5", "--incident-at", "3", "--n-nodes", "6"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "usecase_III_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Hypothesis" in text and "Methods" in text
    assert "Public data used" in text and "Baseline" in text
    assert "Outcomes" in text and "Falsification" in text
    assert "lead time" in text.lower() or "Phase" in text
    assert "Pass" in text


def test_run_usecase_iv_contestability_script(tmp_path: Path) -> None:
    """Usecase PRD IV (useccases.md): run_usecase_iv_contestability.py produces usecase_IV_report.txt with scientific-method sections."""
    r = _run_script("run_usecase_iv_contestability.py", ["--n", "8"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "usecase_IV_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Hypothesis" in text and "Methods" in text
    assert "Public data used" in text and "Baseline" in text
    assert "Outcomes" in text and "Falsification" in text
    assert "Reversal success" in text and "Pass" in text


def test_run_usecase_viii_identity_script(tmp_path: Path) -> None:
    """Usecase PRD VIII (useccases.md): run_usecase_viii_identity.py produces usecase_VIII_report.txt and run_identity.json."""
    r = _run_script("run_usecase_viii_identity.py", ["--seed", "42"], tmp_path)
    assert r.returncode == 0
    report = tmp_path / "usecase_VIII_report.txt"
    assert report.exists()
    identity_path = tmp_path / "run_identity.json"
    assert identity_path.exists()
    text = report.read_text()
    assert "Hypothesis" in text and "Methods" in text
    assert "Public data used" in text and "identity" in text.lower()
    assert "config_hash" in text or "git_commit" in text
    import json
    identity = json.loads(identity_path.read_text())
    assert "seed" in identity and "evaluation_timestamp" in identity
    assert "dataset_version" in identity


def test_run_extended_drift_dashboard_script(tmp_path: Path) -> None:
    """PRD XIV (extendedPRD.md): run_extended_drift_dashboard.py produces extended_drift_report.txt."""
    r = _run_script("run_extended_drift_dashboard.py", ["--n", "6", "--n-steps", "3"], tmp_path)
    assert r.returncode == 0
    report = tmp_path / "extended_drift_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Trajectory" in text or "E_cl" in text
    assert "Baseline" in text and "drift" in text.lower()
    assert "Falsification" in text


def test_run_supervisory_overload_audit_script(tmp_path: Path) -> None:
    """PRD XIII (extendedPRD.md): run_supervisory_overload_audit.py produces supervisory_overload_report.txt."""
    r = _run_script("run_supervisory_overload_audit.py", ["--n", "8", "--bands", "2", "4"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "supervisory_overload_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "detection_rate" in text and "false_reassurance" in text
    assert "Band" in text and "Falsification" in text


def test_run_grace_validation_script(tmp_path: Path) -> None:
    """PRD XII (extendedPRD.md): run_grace_validation.py produces grace_validation_report.txt."""
    r = _run_script("run_grace_validation.py", ["--n", "6"], tmp_path)
    assert r.returncode == 0
    report = tmp_path / "grace_validation_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "coherence" in text and "entropy" in text
    assert "Grace" in text or "grace" in text


def test_run_extended_contestability_legitimacy_script(tmp_path: Path) -> None:
    """PRD XV (extendedPRD.md): run_extended_contestability_legitimacy.py produces extended_contestability_legitimacy_report.txt."""
    r = _run_script("run_extended_contestability_legitimacy.py", ["--n", "8"], tmp_path)
    assert r.returncode in (0, 1)
    report = tmp_path / "extended_contestability_legitimacy_report.txt"
    assert report.exists()
    text = report.read_text()
    assert "Hypothesis" in text and "Methods" in text
    assert "Public data used" in text and "Baseline" in text
    assert "reversal_success" in text and "contestability" in text.lower()
    assert "Falsification" in text


def test_run_aaron_vs_plain_suite_script(tmp_path: Path) -> None:
    """PRD XVII (extendedPRD.md): run_aaron_vs_plain_suite.py produces suite report and findings artifacts."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_aaron_vs_plain_suite.py"), "--out-dir", str(tmp_path), "--n", "6"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"Script failed: {r.stderr}"
    assert (tmp_path / "aaron_vs_plain_suite_report.txt").exists()
    run_dir = tmp_path / "aaron_vs_plain_suite_run"
    assert run_dir.exists()
    assert (run_dir / "boundary_benchmark_report.txt").exists()
    assert (run_dir / "null_rival_audit_report.txt").exists()
    assert (run_dir / "leverage_stability_report.txt").exists()
    text = (tmp_path / "aaron_vs_plain_suite_report.txt").read_text()
    assert "PRD XVII" in text and "Baseline" in text


def test_validate_findings_sections_script() -> None:
    """PRD XVI (extendedPRD.md): validate_findings_sections.py passes on a compliant findings doc."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_findings_sections.py"), str(ROOT / "docs/findings/20260310_usecases_findings.md")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"Validator failed: {r.stderr}"
    assert "OK" in r.stdout


def test_build_public_findings_script(tmp_path: Path) -> None:
    """PRD XII (buttonup): build_public_findings.py produces required public-facing artifacts."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_public_findings.py"), "--out-dir", str(tmp_path), "--runs-dir", str(tmp_path / "runs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"Script failed: {r.stderr}"
    assert (tmp_path / "findings_summary.md").exists()
    assert (tmp_path / "benchmark_leaderboard.csv").exists()
    assert (tmp_path / "null_audit_summary.md").exists()
    assert (tmp_path / "outlier_audit_summary.md").exists()
    assert (tmp_path / "model_registry.csv").exists()
    assert (tmp_path / "failure_gallery.md").exists()
    assert (tmp_path / "dataset_provenance.md").exists()
    text = (tmp_path / "findings_summary.md").read_text()
    assert "Findings Summary" in text
    assert "findings" in text.lower() or "FINDINGS" in text


def test_run_enron_timewindowed_pipeline_script(tmp_path: Path) -> None:
    """Deliverable 2 (organizational_empirical_validation.md): run_enron_timewindowed_pipeline.py produces report with HC_t, C2F_t, baselines."""
    enron_gz = ROOT / "data" / "raw" / "enron_snap" / "email-Enron.txt.gz"
    if not enron_gz.exists():
        pytest.skip("Enron raw data not present (run download_and_normalize.py --source enron_snap)")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_enron_timewindowed_pipeline.py"),
            "--out-dir", str(tmp_path),
            "--n-windows", "2",
            "--max-nodes", "20",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"Script failed: {r.stderr}"
    report = tmp_path / "enron_timewindowed_report.txt"
    assert report.exists(), f"Expected report: {report}"
    text = report.read_text()
    assert "HC_t" in text and "C2F_t" in text and "density" in text and "mean_degree" in text
    assert "Event-linked" in text or "DEFERRED" in text


def test_run_public_data_verification_script_fails_gracefully_without_data(tmp_path: Path) -> None:
    """run_public_data_verification.py exits non-zero when processed dir has no kernel.npz (no Enron data)."""
    # Use a nonexistent processed dir so script fails with clear error
    fake_dir = tmp_path / "nonexistent_enron"
    fake_dir.mkdir()
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_public_data_verification.py"), "--processed-dir", str(fake_dir), "--out", str(tmp_path / "out.txt")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert "Missing" in r.stderr or "kernel.npz" in r.stderr or "FileNotFoundError" in r.stderr or "No such" in r.stderr


def test_generate_verification_report_script_produces_domain_61_report() -> None:
    """BPO verification: generate_verification_report.py produces T3.2, T3.3, T3.4, E6.1 in output (Domain 6.1)."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_verification_report.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"Script failed: {r.stderr}"
    out = r.stdout + r.stderr
    assert "T3.2" in out
    assert "T3.3" in out
    assert "T3.4" in out
    assert "E6.1" in out
    assert "Verification report" in out or "verification_report" in out
