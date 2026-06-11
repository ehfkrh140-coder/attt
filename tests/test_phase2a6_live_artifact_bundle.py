from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from arenas.evm_fork_execution_arena import (
    UNSUPPORTED_EXECUTABLE_FORK_DRILLS,
    EvmForkExecutionArena,
)
from evidence.evidence_quality import EvidenceReadinessVerdict
from evidence.live_artifact_bundle import (
    LiveArtifactKind,
    LiveArtifactStatus,
    load_bundle_from_artifact_dir,
    load_bundle_from_manifest,
    review_live_artifact_bundle,
)
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

CRITICAL_LIVE_REVIEW_FILES = (
    Path("docs/PHASE_2A6_LIVE_ARTIFACT_REVIEW.md"),
    Path("docs/live_artifact_bundle_review.md"),
    Path("docs/PROJECT_STATE_CURRENT.md"),
    Path("evidence/live_artifact_bundle.py"),
    Path("scripts/review_live_artifact_bundle.py"),
    Path("tests/test_phase2a6_live_artifact_bundle.py"),
)


def _generate_fixture_bundle(tmp_path: Path) -> Path:
    generate_evidence_pack(
        local_rpc_url="http://127.0.0.1:8545",
        root_address="aave-root",
        network="ethereum",
        fork_block=None,
        output=str(tmp_path / "aave_v3_evidence_pack.md"),
        export_target=str(tmp_path / "aave_v3_readonly.yaml"),
        export_dependency_review=str(tmp_path / "dependency_graph_review.md"),
        fixture_readonly=True,
    )
    return tmp_path


def _generate_live_local_bundle(tmp_path: Path) -> Path:
    _generate_fixture_bundle(tmp_path)
    evidence_path = tmp_path / "aave_v3_evidence_pack.md"
    evidence_text = evidence_path.read_text(encoding="utf-8")
    evidence_text = evidence_text.replace("Evidence source: fixture-backed", "Evidence source: live-local")
    evidence_text = evidence_text.replace("Local fork reachable: no", "Local fork reachable: yes")
    evidence_text = evidence_text.replace("fixture-local-rpc", "localhost-local-rpc")
    evidence_text = evidence_text.replace("blocked_fixture_only", "live_readonly_review")
    evidence_text = evidence_text.replace("fixture_review_candidate", "live_readonly_review_candidate")
    evidence_text = evidence_text.replace("fixture-backed evidence", "user-provided read-only evidence")
    evidence_text = evidence_text.replace("fixture_only", "readonly_only")
    evidence_text += "\n- Read-only localhost workflow: yes\n- Transactions sent: no\n"
    evidence_path.write_text(evidence_text, encoding="utf-8")

    target_path = tmp_path / "aave_v3_readonly.yaml"
    data = yaml.safe_load(target_path.read_text(encoding="utf-8"))
    data["evidence_source"] = "live_readonly"
    data["deployment_sources"] = ["local_evm_fork_twin_readonly"]
    target_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    dependency_path = tmp_path / "dependency_graph_review.md"
    dependency_text = dependency_path.read_text(encoding="utf-8")
    dependency_text = dependency_text.replace("fixture_review_candidate", "live_readonly_review_candidate")
    dependency_path.write_text(dependency_text, encoding="utf-8")

    smoke_path = tmp_path / "manual_live_fork_smoke_result.md"
    smoke_path.write_text(
        "# Manual Live Fork Smoke Result\n\n"
        "- Source: user-provided live-local read-only artifact\n"
        "- Endpoint class: localhost\n"
        "- Read-only mode: yes\n"
        "- Transactions sent: no\n",
        encoding="utf-8",
    )
    return tmp_path


def _intent() -> LocalTxIntent:
    return LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-live-artifact-review-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="phase2a6-live-review",
    )


def _finding_status(review, kind: LiveArtifactKind) -> LiveArtifactStatus:
    finding = review.finding_for(kind)
    assert finding is not None
    return finding.status


def test_missing_artifact_directory_is_handled_safely(tmp_path: Path) -> None:
    bundle = load_bundle_from_artifact_dir(tmp_path / "missing-bundle-dir")
    review = review_live_artifact_bundle(bundle)
    assert "missing-artifact-dir" in review.source
    assert review.evidence_quality_report is None
    assert review.phase2b_enabled is False
    assert "Phase 2B execution enabled: no" in review.to_markdown()


def test_missing_bundle_manifest_is_handled_safely(tmp_path: Path) -> None:
    bundle = load_bundle_from_manifest(tmp_path / "missing_bundle_manifest.yaml")
    review = review_live_artifact_bundle(bundle)
    assert "missing-manifest" in review.source
    assert review.evidence_quality_report is None
    assert _finding_status(review, LiveArtifactKind.EVIDENCE_PACK) == LiveArtifactStatus.MISSING


def test_partial_artifact_bundle_is_review_incomplete_not_execution_ready(tmp_path: Path) -> None:
    (tmp_path / "aave_v3_evidence_pack.md").write_text(
        "# Evidence Pack\n\n- Evidence source: fixture-backed\n",
        encoding="utf-8",
    )
    review = review_live_artifact_bundle(load_bundle_from_artifact_dir(tmp_path))
    assert _finding_status(review, LiveArtifactKind.EVIDENCE_PACK) == LiveArtifactStatus.FIXTURE_BACKED
    assert review.evidence_quality_report is None
    assert "execution approval" in review.to_markdown()


def test_fixture_backed_artifacts_are_classified_and_not_execution_ready(tmp_path: Path) -> None:
    _generate_fixture_bundle(tmp_path)
    review = review_live_artifact_bundle(load_bundle_from_artifact_dir(tmp_path))
    assert _finding_status(review, LiveArtifactKind.EVIDENCE_PACK) == LiveArtifactStatus.FIXTURE_BACKED
    assert _finding_status(review, LiveArtifactKind.TARGET_MANIFEST) == LiveArtifactStatus.FIXTURE_BACKED
    assert review.evidence_quality_report is not None
    assert review.evidence_quality_report.final_readiness_verdict == (
        EvidenceReadinessVerdict.FIXTURE_ONLY_NOT_EXECUTION_READY
    )
    assert review.execution_permission_granted is False


def test_localhost_live_local_readonly_artifacts_are_review_ready_only(tmp_path: Path) -> None:
    _generate_live_local_bundle(tmp_path)
    review = review_live_artifact_bundle(load_bundle_from_artifact_dir(tmp_path))
    assert _finding_status(review, LiveArtifactKind.EVIDENCE_PACK) == LiveArtifactStatus.LIVE_LOCAL
    assert _finding_status(review, LiveArtifactKind.MANUAL_LIVE_SMOKE) == LiveArtifactStatus.LIVE_LOCAL
    assert review.evidence_quality_report is not None
    assert review.evidence_quality_report.final_readiness_verdict == (
        EvidenceReadinessVerdict.LIVE_READONLY_EVIDENCE_REVIEW_READY
    )
    markdown = review.to_markdown()
    assert "Evidence quality grants execution: no" in markdown
    assert "Execution permission granted: no" in markdown


@pytest.mark.parametrize(
    ("unsafe_text", "forbidden_echo"),
    (
        ("endpoint: https://mainnet.example.invalid", "https://mainnet.example.invalid"),
        ("operator_private_key: demo-secret", "operator_private_key"),
        ("raw_calldata: reusable-bytes", "raw_calldata"),
        ("transaction bundle: bundled-payload", "transaction bundle"),
        ("live victim list: target-one", "target-one"),
    ),
)
def test_unsafe_artifacts_are_blocked_and_contents_are_not_printed(
    tmp_path: Path,
    unsafe_text: str,
    forbidden_echo: str,
) -> None:
    (tmp_path / "aave_v3_evidence_pack.md").write_text(unsafe_text, encoding="utf-8")
    review = review_live_artifact_bundle(load_bundle_from_artifact_dir(tmp_path))
    assert _finding_status(review, LiveArtifactKind.EVIDENCE_PACK) == LiveArtifactStatus.UNSAFE
    markdown = review.to_markdown()
    assert forbidden_echo not in markdown
    assert "Unsafe artifact content printed: no" in markdown
    assert "blocked" not in forbidden_echo.lower() or "blocked" in markdown.lower()


def test_bundle_manifest_feeds_existing_evidence_quality_path(tmp_path: Path) -> None:
    _generate_fixture_bundle(tmp_path)
    manifest = tmp_path / "live_artifact_bundle.yaml"
    manifest.write_text(
        "artifacts:\n"
        "  evidence_pack: aave_v3_evidence_pack.md\n"
        "  target_manifest: aave_v3_readonly.yaml\n"
        "  dependency_graph_review: dependency_graph_review.md\n",
        encoding="utf-8",
    )
    review = review_live_artifact_bundle(load_bundle_from_manifest(manifest))
    assert review.evidence_quality_report is not None
    assert "Existing evidence quality review: run" in review.to_markdown()


def test_bundle_review_fixture_demo_script_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    command = [
        sys.executable,
        "scripts/review_live_artifact_bundle.py",
        "--fixture-demo",
        "--output",
    ]
    subprocess.run(command + [str(first)], check=True, capture_output=True, text=True)
    subprocess.run(command + [str(second)], check=True, capture_output=True, text=True)
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
    assert "# Live Artifact Bundle Review" in first.read_text(encoding="utf-8")


def test_generated_bundle_review_report_is_sanitized() -> None:
    text = Path("docs/live_artifact_bundle_review.md").read_text(encoding="utf-8")
    forbidden = (
        "raw_calldata",
        "calldata:",
        "transaction bundle:",
        "private_key",
        "seed phrase",
        "https://",
        "infura",
        "alchemy",
        "quicknode",
        "public-network portable exploit",
    )
    assert all(token not in text.lower() for token in forbidden)
    assert "Execution permission granted: no" in text
    assert "Phase 2B execution enabled: no" in text


def test_live_artifact_review_files_are_readable_and_have_no_bidi_controls() -> None:
    minimum_lines = {
        "docs/PHASE_2A6_LIVE_ARTIFACT_REVIEW.md": 50,
        "docs/live_artifact_bundle_review.md": 20,
        "evidence/live_artifact_bundle.py": 120,
        "scripts/review_live_artifact_bundle.py": 50,
        "tests/test_phase2a6_live_artifact_bundle.py": 150,
    }
    for path in CRITICAL_LIVE_REVIEW_FILES:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert len(lines) >= minimum_lines.get(str(path), 20), path
        assert max(len(line) for line in lines) <= 140, path
        bidi = [
            (line_number, hex(ord(ch)))
            for line_number, line in enumerate(lines, start=1)
            for ch in line
            if ord(ch) in BIDI_CONTROL_CODEPOINTS
        ]
        assert not bidi, (path, bidi[:5])


def test_no_phase2a6_live_review_verdict_grants_execution() -> None:
    assert "EXECUTION_READY" not in EvidenceReadinessVerdict.__members__
    text = Path("docs/live_artifact_bundle_review.md").read_text(encoding="utf-8")
    assert "Execution permission granted: no" in text
    assert "Evidence quality grants execution: no" in text


def test_live_artifact_bundle_python_files_compile() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "evidence/live_artifact_bundle.py",
            "scripts/review_live_artifact_bundle.py",
        ],
        check=True,
    )


def test_phase2b_execution_remains_disabled_for_live_artifact_review() -> None:
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(_intent())
