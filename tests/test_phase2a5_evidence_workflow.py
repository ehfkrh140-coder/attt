from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from core.errors import SafetyGuardError
from core.safety import SafetyGuard
from evidence.live_fork_evidence import (
    AaveReadOnlyDiscoveryEvidence,
    DependencyGraphReviewEvidence,
    LiveForkEvidencePack,
    LocalForkCheckEvidence,
    TargetManifestReviewEvidence,
)
from scripts.generate_dependency_graph_review import generate_dependency_review
from scripts.generate_live_fork_evidence_pack import generate_evidence_pack
from scripts.phase2b_preflight import run_preflight
from scripts.review_target_manifest import render_manifest_review, review_manifest

ROOT = Path(__file__).resolve().parents[1]
SELECTORS = ["0x026b1d5f", "0xd1946dbc", "0x35ea6a75", "0xc44b11f7", "0xb3596f07", "0x0fcfa7c4"]


def _sample_pack() -> LiveForkEvidencePack:
    return LiveForkEvidencePack(
        created_at="2026-06-10T00:00:00+00:00",
        protocol="aave_v3",
        network="ethereum",
        fork_block="not-recorded",
        local_rpc_url_label="http://127.0.0.1:local",
        evidence_source="fixture-backed",
        local_fork=LocalForkCheckEvidence(False, "fixture", "fixture", True, False, "FIXTURE_ONLY", ["fixture-backed evidence"]),
        aave_discovery=AaveReadOnlyDiscoveryEvidence(
            protocol="aave_v3",
            protocol_twin_mode="evm_fork_twin",
            root_address_label="aave-root",
            discovery_status="fully_discovered",
            core_contracts_count=6,
            reserve_count=2,
            max_reserves_requested=8,
            max_reserves_processed=8,
            truncated=False,
            watch_items=["reserve_oracle_dependency"],
            selected_drill_recommendations=["oracle_divergence_drill"],
            recon_hypotheses_count=4,
            execution_gated=True,
            mockarena_fallback=False,
        ),
        target_manifest=TargetManifestReviewEvidence("aave_v3_readonly.yaml", True, False, False, False, True, 11, 2, True, []),
        dependency_graph_review=DependencyGraphReviewEvidence("dependency_graph_review.md", True, 2, 4, 2, 1, 0, "fixture_review_candidate"),
        phase2b_candidate_status="blocked_fixture_only",
        missing_prerequisites=["live local fork evidence", "reviewer scope confirmation"],
    )


def _generate_fixture_artifacts(tmp_path: Path):
    evidence_path = tmp_path / "aave_v3_evidence_pack.md"
    target_path = tmp_path / "aave_v3_readonly.yaml"
    review_path = tmp_path / "dependency_graph_review.md"
    pack, output = generate_evidence_pack(
        local_rpc_url="http://127.0.0.1:8545",
        root_address="aave-root",
        network="ethereum",
        fork_block=None,
        output=str(evidence_path),
        export_target=str(target_path),
        export_dependency_review=str(review_path),
        fixture_readonly=True,
    )
    return pack, output, evidence_path, target_path, review_path


def test_live_fork_evidence_models_safe_summary():
    summary = _sample_pack().safe_summary()
    SafetyGuard().assert_safe_report(summary)
    assert "Phase 2B candidate status: blocked_fixture_only" in summary
    assert "Selected drill recommendations gated: oracle_divergence_drill (gated)" in summary


def test_live_fork_evidence_pack_contains_no_unsafe_artifacts():
    summary = _sample_pack().safe_summary()
    assert "raw_calldata" not in summary
    assert "eth_sendTransaction" not in summary
    assert all(selector not in summary for selector in SELECTORS)


def test_evidence_pack_tracks_missing_prerequisites():
    pack = _sample_pack()
    assert "live local fork evidence" in pack.missing_prerequisites
    assert "reviewer scope confirmation" in pack.safe_summary()


def test_evidence_pack_records_phase2b_blocked_by_default():
    assert _sample_pack().phase2b_candidate_status == "blocked_fixture_only"
    assert "Phase 2B execution enabled: no" in _sample_pack().safe_summary()


def test_generate_evidence_pack_fixture_mode_writes_files(tmp_path: Path):
    pack, output, evidence_path, target_path, review_path = _generate_fixture_artifacts(tmp_path)
    assert evidence_path.exists() and target_path.exists() and review_path.exists()
    assert pack.evidence_source == "fixture-backed"
    assert pack.aave_discovery.reserve_count == 2
    assert "Evidence source: fixture-backed" in output
    SafetyGuard().assert_safe_report(output)


def test_generate_evidence_pack_unavailable_live_fork_is_safe(tmp_path: Path):
    pack, output = generate_evidence_pack(
        local_rpc_url="http://127.0.0.1:1",
        root_address="aave-root",
        network="ethereum",
        fork_block=None,
        output=str(tmp_path / "evidence.md"),
        export_target=str(tmp_path / "target.yaml"),
        export_dependency_review=str(tmp_path / "review.md"),
        fixture_readonly=False,
    )
    assert pack.local_fork.reachable is False
    assert pack.phase2b_candidate_status == "blocked_missing_prerequisites"
    assert "LOCAL_FORK_UNAVAILABLE" in output
    SafetyGuard().assert_safe_report(output)


def test_generate_evidence_pack_output_contains_phase2b_blocked(tmp_path: Path):
    pack, output, *_ = _generate_fixture_artifacts(tmp_path)
    assert pack.phase2b_candidate_status == "blocked_fixture_only"
    assert "Phase 2B candidate status: blocked_fixture_only" in output


def test_generate_evidence_pack_does_not_require_live_fork_in_ci(tmp_path: Path):
    pack, _output, *_ = _generate_fixture_artifacts(tmp_path)
    assert pack.local_fork.safety_status == "FIXTURE_ONLY"


def test_generate_evidence_pack_rejects_public_rpc(tmp_path: Path):
    with pytest.raises(SafetyGuardError):
        generate_evidence_pack(
            local_rpc_url="https://example.invalid/rpc",
            root_address="aave-root",
            network="ethereum",
            fork_block=None,
            output=str(tmp_path / "evidence.md"),
            export_target=None,
            export_dependency_review=None,
            fixture_readonly=False,
        )


def test_generate_evidence_pack_contains_no_raw_selectors(tmp_path: Path):
    _pack, output, evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    combined = output + evidence_path.read_text() + review_path.read_text()
    assert all(selector not in combined for selector in SELECTORS)
    SafetyGuard().assert_safe_report(combined)


def test_dependency_graph_review_generator_writes_safe_markdown(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    evidence, markdown = generate_dependency_review(target_path, tmp_path / "review2.md")
    assert evidence.exists
    assert "Dependency Graph Review Candidate" in markdown
    SafetyGuard().assert_safe_report(markdown)


def test_dependency_graph_review_includes_reserve_paths(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    evidence, _markdown = generate_dependency_review(target_path, tmp_path / "review2.md")
    assert evidence.reserve_paths_count >= 2
    assert evidence.debt_paths_count >= 2


def test_dependency_graph_review_includes_watch_items(tmp_path: Path):
    _pack, _output, _evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    text = review_path.read_text()
    assert "Watch items count:" in text
    assert "reserve_oracle_dependency" in text


def test_dependency_graph_review_does_not_confirm_scope(tmp_path: Path):
    _pack, _output, _evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    assert "Scope confirmed by this review: no" in review_path.read_text()


def test_dependency_graph_review_contains_no_unsafe_artifacts(tmp_path: Path):
    _pack, _output, _evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    text = review_path.read_text()
    assert all(selector not in text for selector in SELECTORS)
    SafetyGuard().assert_safe_report(text)


def test_review_target_manifest_passes_safe_readonly_manifest(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    evidence = review_manifest(target_path)
    rendered = render_manifest_review(evidence)
    assert "Manifest review: PASS" in rendered
    assert evidence.read_only_only and not evidence.executable_drills_allowed


def test_review_target_manifest_fails_if_scope_confirmed(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    data = yaml.safe_load(target_path.read_text())
    data["scope_confirmed"] = True
    target_path.write_text(yaml.safe_dump(data))
    assert "Manifest review: FAIL" in render_manifest_review(review_manifest(target_path))


def test_review_target_manifest_fails_if_execution_allowed(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    data = yaml.safe_load(target_path.read_text())
    data["executable_drills_allowed"] = True
    target_path.write_text(yaml.safe_dump(data))
    evidence = review_manifest(target_path)
    assert evidence.executable_drills_allowed
    assert "Manifest review: FAIL" in render_manifest_review(evidence)


def test_review_target_manifest_rejects_unsafe_artifacts(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    data = yaml.safe_load(target_path.read_text())
    data["raw_calldata"] = "unsafe"
    target_path.write_text(yaml.safe_dump(data))
    assert "unsafe_token_raw_calldata" in review_manifest(target_path).safety_notes


def test_review_target_manifest_does_not_mutate_manifest(tmp_path: Path):
    _pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    before = target_path.read_text()
    review_manifest(target_path)
    assert target_path.read_text() == before


def test_preflight_consumes_evidence_pack(tmp_path: Path):
    _pack, _output, evidence_path, target_path, review_path = _generate_fixture_artifacts(tmp_path)
    output = run_preflight("missing.md", str(target_path), str(review_path), evidence_pack=str(evidence_path))
    assert "Evidence pack: present" in output
    assert "Evidence source: fixture-backed" in output


def test_preflight_fails_fixture_only_evidence(tmp_path: Path):
    _pack, _output, evidence_path, target_path, review_path = _generate_fixture_artifacts(tmp_path)
    output = run_preflight("missing.md", str(target_path), str(review_path), evidence_pack=str(evidence_path))
    assert "Phase 2B readiness: FAIL" in output
    assert "fixture-backed evidence is not enough" in output


def test_preflight_fails_missing_dependency_review(tmp_path: Path):
    _pack, _output, evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    output = run_preflight("missing.md", str(target_path), str(tmp_path / "missing_review.md"), evidence_pack=str(evidence_path))
    assert "dependency graph review" in output
    assert "Phase 2B readiness: FAIL" in output


def test_preflight_fails_unconfirmed_manifest(tmp_path: Path):
    _pack, _output, evidence_path, target_path, review_path = _generate_fixture_artifacts(tmp_path)
    output = run_preflight("missing.md", str(target_path), str(review_path), evidence_pack=str(evidence_path))
    assert "target manifest scope unconfirmed" in output


def test_preflight_reports_review_ready_only_when_artifacts_exist(tmp_path: Path):
    _pack, _output, evidence_path, target_path, review_path = _generate_fixture_artifacts(tmp_path)
    evidence_text = evidence_path.read_text().replace("Evidence source: fixture-backed", "Evidence source: live-local").replace("Phase 2B candidate status: blocked_fixture_only", "Phase 2B candidate status: review_candidate_only")
    evidence_path.write_text(evidence_text)
    manual = tmp_path / "manual_smoke.md"
    manual.write_text("Manual live fork smoke result\n- No transaction sent confirmation: yes\n")
    output = run_preflight(str(manual), str(target_path), str(review_path), reviewer_confirms_scope=True, evidence_pack=str(evidence_path))
    assert "Phase 2B readiness: REVIEW_READY" in output
    assert "Execution enabled: no" in output


def test_preflight_still_does_not_enable_execution(tmp_path: Path):
    _pack, _output, evidence_path, target_path, review_path = _generate_fixture_artifacts(tmp_path)
    output = run_preflight("missing.md", str(target_path), str(review_path), evidence_pack=str(evidence_path))
    assert "Execution enabled: no" in output
    assert "Executable fork drills enabled: no" in output


def test_evidence_manifest_reserve_count_consistency(tmp_path: Path):
    pack, _output, _evidence_path, target_path, _review_path = _generate_fixture_artifacts(tmp_path)
    manifest = yaml.safe_load(target_path.read_text())
    metadata = manifest["protocol_metadata"]["aave_v3"]
    assert pack.aave_discovery.reserve_count == metadata["reserve_count"] == len(metadata["reserves"])


def test_evidence_dependency_review_watch_item_consistency(tmp_path: Path):
    pack, _output, _evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    text = review_path.read_text()
    for item in pack.aave_discovery.watch_items:
        assert item in text


def test_gated_drill_recommendations_are_consistent(tmp_path: Path):
    pack, _output, evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    combined = evidence_path.read_text() + "\n" + review_path.read_text()
    for drill in pack.aave_discovery.selected_drill_recommendations:
        assert f"{drill} (gated)" in combined


def test_partial_discovery_keeps_phase2b_blocked():
    pack = replace(_sample_pack(), aave_discovery=replace(_sample_pack().aave_discovery, discovery_status="partially_discovered"), phase2b_candidate_status="blocked_missing_prerequisites")
    assert "blocked" in pack.phase2b_candidate_status


def test_verify_mvp_includes_phase2a5_evidence_pack():
    text = (ROOT / "scripts" / "verify_mvp.py").read_text()
    assert "Phase 2A.5 evidence pack fixture smoke" in text
    assert "Phase 2A.5 preflight remains blocked" in text


def test_verify_mvp_phase2a5_outputs_safe(tmp_path: Path):
    _pack, output, evidence_path, _target_path, review_path = _generate_fixture_artifacts(tmp_path)
    SafetyGuard().assert_safe_report(output + evidence_path.read_text() + review_path.read_text())


def test_docs_explain_phase2a5_evidence_pack():
    docs = (ROOT / "README.md").read_text() + (ROOT / "docs" / "BEGINNER_RUNBOOK.md").read_text()
    assert "Phase 2A.5" in docs and "evidence pack" in docs


def test_docs_say_fixture_evidence_not_enough_for_phase2b():
    docs = (ROOT / "README.md").read_text() + (ROOT / "docs" / "PHASE_2A_DEPTH_AUDIT.md").read_text()
    assert "Fixture" in docs and "not enough for Phase 2B" in docs


def test_docs_say_reviews_do_not_enable_execution():
    docs = (ROOT / "README.md").read_text() + (ROOT / "docs" / "PHASE_2B_PREFLIGHT.md").read_text()
    assert "review artifact" in docs and "not execution" in docs.lower()


def test_docs_say_phase2b_remains_blocked():
    docs = (ROOT / "README.md").read_text() + (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
    assert "Phase 2B remains blocked" in docs


def test_evidence_pack_cli_fixture_mode_writes_files(tmp_path: Path):
    evidence_path = tmp_path / "evidence.md"
    target_path = tmp_path / "target.yaml"
    review_path = tmp_path / "review.md"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_live_fork_evidence_pack.py",
            "--fixture-readonly",
            "--root-address",
            "aave-root",
            "--output",
            str(evidence_path),
            "--export-target",
            str(target_path),
            "--export-dependency-review",
            str(review_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert evidence_path.exists() and target_path.exists() and review_path.exists()
    assert "blocked_fixture_only" in result.stdout
