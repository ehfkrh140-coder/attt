from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from arenas.evm_fork_execution_arena import EvmForkExecutionArena, UNSUPPORTED_EXECUTABLE_FORK_DRILLS
from core.capability_boundary import validate_matrix_complete
from evidence.evidence_quality import EvidenceReadinessVerdict, EvidenceSourceType, review_evidence_quality
from redteam.local_tx_intent import LocalTxIntent
from scripts.generate_live_fork_evidence_pack import generate_evidence_pack


BIDI_CONTROL_CODEPOINTS = {
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2066,
    0x2067,
    0x2068,
    0x2069,
}

CRITICAL_FORMAT_FILES = (
    Path("docs/PROJECT_STATE_CURRENT.md"),
    Path("docs/live_fork_evidence_quality_report.md"),
    Path("docs/SAFETY_BOUNDARY_MODEL.md"),
    Path("docs/CAPABILITY_STATUS.md"),
    Path("docs/PHASE_2B_READINESS_CHECKLIST.md"),
    Path("evidence/evidence_quality.py"),
    Path("scripts/review_live_fork_evidence_quality.py"),
    Path("tests/test_phase2a6_evidence_quality_review.py"),
)


def _generate_fixture_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    evidence_path = tmp_path / "aave_v3_evidence_pack.md"
    target_path = tmp_path / "aave_v3_readonly.yaml"
    dependency_path = tmp_path / "dependency_graph_review.md"
    generate_evidence_pack(
        local_rpc_url="http://127.0.0.1:8545",
        root_address="aave-root",
        network="ethereum",
        fork_block=None,
        output=str(evidence_path),
        export_target=str(target_path),
        export_dependency_review=str(dependency_path),
        fixture_readonly=True,
    )
    return evidence_path, target_path, dependency_path


def _intent() -> LocalTxIntent:
    return LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-quality-review-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="phase2a6-review",
    )


def test_fixture_only_evidence_cannot_approve_phase2b(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    assert report.source_type == EvidenceSourceType.FIXTURE_BACKED
    assert report.final_readiness_verdict == EvidenceReadinessVerdict.FIXTURE_ONLY_NOT_EXECUTION_READY
    assert any(blocker.code == "fixture_only_evidence" for blocker in report.phase2b_blockers.blockers)
    assert "EXECUTION_READY" not in EvidenceReadinessVerdict.__members__


def test_missing_live_fork_evidence_is_review_finding_or_blocker(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    blocker_codes = {blocker.code for blocker in report.phase2b_blockers.blockers}
    triage_categories = {item.category for item in report.triage.items}
    assert "live_local_readonly_evidence_missing" in blocker_codes
    assert "manual_live_smoke" in triage_categories


def test_missing_required_inputs_are_handled_safely(tmp_path: Path) -> None:
    report = review_evidence_quality(
        evidence_pack=tmp_path / "missing_pack.md",
        target_manifest=tmp_path / "missing_target.yaml",
        dependency_graph_review=tmp_path / "missing_dependency.md",
    )
    markdown = report.to_markdown()
    assert report.final_readiness_verdict == EvidenceReadinessVerdict.REVIEW_INCOMPLETE
    assert "missing_pack.md: missing" in markdown
    assert "missing_target.yaml: missing" in markdown
    assert "missing_dependency.md: missing" in markdown
    assert "Execution permission granted: no" in markdown


def test_decode_unavailable_and_unresolved_fields_become_triage_items(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    data = yaml.safe_load(target_path.read_text())
    aave = data["protocol_metadata"]["aave_v3"]
    aave["unresolved_calls"] = ["aave_pool_get_reserve_data"]
    aave["unresolved_reserve_fields"] = ["oracle_source"]
    aave["reserves"][0]["discovery_status"] = "decode_unavailable"
    aave["reserves"][0]["unresolved_fields"] = ["a_token"]
    target_path.write_text(yaml.safe_dump(data, sort_keys=False))

    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    assert report.abi_compatibility.decode_unavailable_count >= 2
    assert report.reserve_coverage.unresolved_reserve_fields_count >= 2
    assert any(item.category == "abi_decode" for item in report.triage.items)
    assert any(item.category == "reserve_coverage" for item in report.triage.items)


def test_reserve_coverage_is_scored_and_gaps_are_reported(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    assert report.reserve_coverage.reserve_count == 2
    assert report.reserve_coverage.max_reserves_processed == 8
    assert report.reserve_coverage.score < 1.0
    assert any(finding.label == "reserve_coverage_gap" for finding in report.reserve_coverage.findings)


def test_abi_compatibility_risks_are_reported(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    data = yaml.safe_load(target_path.read_text())
    data["protocol_metadata"]["aave_v3"]["reserve_discovery_status"] = "partial"
    target_path.write_text(yaml.safe_dump(data, sort_keys=False))
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    assert any(finding.label == "discovery_status" for finding in report.abi_compatibility.findings)
    assert any(item.category == "abi_decode" for item in report.triage.items)


def test_report_output_is_sanitized(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    markdown = report.to_markdown().lower()
    forbidden = [
        "raw_calldata",
        "raw calldata",
        "transaction bundle",
        "transaction bundles",
        "private_key",
        "private key",
        "mnemonic",
        "seed phrase",
        "reusable transaction payload",
        "public-network portable exploit artifact",
        "infura",
        "alchemy",
        "quicknode",
        "ankr",
        "blastapi",
        "publicnode",
    ]
    assert all(token not in markdown for token in forbidden)
    assert "phase 2b execution enabled: no" in markdown
    assert "aave red drills executed by this review: no" in markdown


def test_review_script_generates_deterministic_markdown_from_fixture_inputs(tmp_path: Path) -> None:
    output_path = tmp_path / "quality_report.md"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/review_live_fork_evidence_quality.py",
            "--fixture-demo",
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    output_text = output_path.read_text()
    assert output_text == result.stdout.rstrip("\n") + "\n"
    assert "# Live Fork Evidence Quality Report" in output_text
    assert "Final readiness verdict (review-only): FIXTURE_ONLY_NOT_EXECUTION_READY" in output_text
    assert "Execution permission granted: no" in output_text


def test_live_readonly_review_ready_is_not_execution_permission(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    smoke_path = tmp_path / "manual_live_smoke.md"
    smoke_path.write_text("Manual Live Fork Smoke Result\n- Review status: present\n")
    evidence_text = evidence_path.read_text().replace("Evidence source: fixture-backed", "Evidence source: live-local")
    evidence_text = evidence_text.replace("Local fork reachable: no", "Local fork reachable: yes")
    evidence_path.write_text(evidence_text)
    data = yaml.safe_load(target_path.read_text())
    data["evidence_source"] = "live_readonly"
    data["deployment_sources"] = ["local_evm_fork_twin_readonly"]
    target_path.write_text(yaml.safe_dump(data, sort_keys=False))
    dep_text = dependency_path.read_text().replace("fixture_review_candidate", "live_readonly_review_candidate")
    dependency_path.write_text(dep_text)

    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
        manual_live_smoke_result=smoke_path,
    )
    assert report.final_readiness_verdict == EvidenceReadinessVerdict.LIVE_READONLY_EVIDENCE_REVIEW_READY
    assert any(blocker.code == "execution_permission_not_granted" for blocker in report.phase2b_blockers.blockers)
    assert "Phase 2B execution enabled: no" in report.to_markdown()


def test_malformed_yaml_target_manifest_is_handled_safely(tmp_path: Path) -> None:
    evidence_path, _target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    malformed = tmp_path / "malformed_target.yaml"
    malformed.write_text("protocol_name: [unterminated\n")
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=malformed,
        dependency_graph_review=dependency_path,
    )
    markdown = report.to_markdown()
    assert report.final_readiness_verdict == EvidenceReadinessVerdict.REVIEW_INCOMPLETE
    assert "manifest_parse_status: malformed (blocker)" in markdown
    assert "Execution permission granted: no" in markdown


def test_unknown_evidence_source_is_handled_safely(tmp_path: Path) -> None:
    evidence_path, target_path, dependency_path = _generate_fixture_inputs(tmp_path)
    evidence_path.write_text("Live Fork Evidence Pack\n- Evidence source: unknown-source\n")
    data = yaml.safe_load(target_path.read_text())
    data["evidence_source"] = "unknown"
    data["deployment_sources"] = ["local_evm_fork_twin_readonly"]
    target_path.write_text(yaml.safe_dump(data, sort_keys=False))
    report = review_evidence_quality(
        evidence_pack=evidence_path,
        target_manifest=target_path,
        dependency_graph_review=dependency_path,
    )
    assert report.source_type == EvidenceSourceType.UNKNOWN
    assert report.final_readiness_verdict == EvidenceReadinessVerdict.BLOCKED_FOR_PHASE_2B
    assert any(item.category == "live_evidence" for item in report.triage.items)


def test_critical_source_and_docs_are_readable_multiline_files() -> None:
    minimum_lines = {
        "evidence/evidence_quality.py": 100,
        "scripts/review_live_fork_evidence_quality.py": 50,
        "tests/test_phase2a6_evidence_quality_review.py": 100,
    }
    for path in CRITICAL_FORMAT_FILES:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert len(lines) >= minimum_lines.get(str(path), 20), path
        assert max(len(line) for line in lines) <= 140, path
        if path.suffix == ".md":
            assert sum(1 for line in lines if line.startswith("## ")) >= 2, path


def test_critical_source_and_docs_have_no_bidi_controls() -> None:
    for path in CRITICAL_FORMAT_FILES:
        text = path.read_text(encoding="utf-8")
        bidi = [
            (line_number, hex(ord(ch)))
            for line_number, line in enumerate(text.splitlines(), start=1)
            for ch in line
            if ord(ch) in BIDI_CONTROL_CODEPOINTS
        ]
        assert not bidi, (path, bidi[:5])


def test_generated_report_has_visible_required_sections() -> None:
    text = Path("docs/live_fork_evidence_quality_report.md").read_text(encoding="utf-8")
    required_sections = [
        "## 1. Summary",
        "## 2. Evidence source classification",
        "## 3. Evidence completeness",
        "## 4. ABI compatibility and decode quality",
        "## 5. Aave reserve coverage",
        "## 6. Dependency graph review quality",
        "## 7. Target manifest review quality",
        "## 8. Discovery triage items",
        "## 9. Phase 2B blocker summary",
        "## 10. Safety and containment confirmation",
        "## 11. Final readiness verdict",
    ]
    for section in required_sections:
        assert section in text


def test_evidence_quality_python_files_compile() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "evidence/evidence_quality.py",
            "scripts/review_live_fork_evidence_quality.py",
        ],
        check=True,
    )


def test_phase2b_execution_remains_disabled() -> None:
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(_intent())


def test_phase2a5r_capability_matrix_remains_intact() -> None:
    assert validate_matrix_complete()
