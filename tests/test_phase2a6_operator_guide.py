from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from arenas.evm_fork_execution_arena import (
    UNSUPPORTED_EXECUTABLE_FORK_DRILLS,
    EvmForkExecutionArena,
)
from redteam.local_tx_intent import LocalTxIntent
from scripts.verify_codex_review_packet import verify_packet_text

SAMPLE_DIR = Path("docs/examples/phase2a6_live_bundle")
SAMPLE_MANIFEST = SAMPLE_DIR / "live_artifact_bundle.yaml"
OP_PACKET = Path("docs/reviews/PHASE_2A6_OP_REVIEW_PACKET.md")

FORBIDDEN_SAMPLE_TOKENS = (
    "private_key",
    "private key",
    "seed phrase",
    "raw_calldata",
    "raw calldata",
    "transaction bundle",
    "selector:",
    "https://",
    "infura",
    "alchemy",
    "quicknode",
    "live victim",
    "victim address",
    "replayable exploit",
)


def _intent() -> LocalTxIntent:
    return LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-operator-guide-validation-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="phase2a6-op-review",
    )


def _run_bundle_review(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, "scripts/review_live_artifact_bundle.py", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_operator_guide_exists_and_contains_safety_assumptions() -> None:
    text = Path("docs/PHASE_2A6_OPERATOR_GUIDE.md").read_text(encoding="utf-8")
    required = (
        "Required safety assumptions",
        "Localhost-only requirement",
        "Do not send transactions",
        "Do not include private keys",
        "Do not include raw calldata or transaction bundles",
        "Do not include live victim targeting data",
        "Phase 2B remains disabled",
    )
    for phrase in required:
        assert phrase in text


def test_manual_review_checklist_exists_and_requires_no_execution_signoff() -> None:
    text = Path("docs/PHASE_2A6_MANUAL_REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    required = (
        "Artifact source classification",
        "Localhost-only verification",
        "ABI/decode triage findings are reviewed",
        "Reserve coverage findings are reviewed",
        "Reports clearly state execution permission is not granted",
        "I confirm review success is not execution permission",
        "I confirm executable fork drills remain blocked",
    )
    for phrase in required:
        assert phrase in text


def test_safe_sample_bundle_files_exist() -> None:
    required_files = (
        "README.md",
        "live_artifact_bundle.yaml",
        "aave_v3_evidence_pack.md",
        "aave_v3_readonly.yaml",
        "dependency_graph_review.md",
        "manual_live_fork_smoke_result.md",
        "phase2b_preflight.md",
    )
    for name in required_files:
        assert (SAMPLE_DIR / name).exists(), name


def test_sample_bundle_contains_no_forbidden_artifacts() -> None:
    for path in SAMPLE_DIR.iterdir():
        if path.is_file():
            text = path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_SAMPLE_TOKENS:
                assert token not in text, (path, token)


def test_sample_artifact_directory_review_passes_and_is_sanitized(tmp_path: Path) -> None:
    output = tmp_path / "sample_dir_review.md"
    stdout = _run_bundle_review(
        "--artifact-dir",
        str(SAMPLE_DIR),
        "--output",
        str(output),
    )
    text = output.read_text(encoding="utf-8")
    assert stdout.rstrip("\n") + "\n" == text
    assert "Evidence quality review ran: yes" in text
    assert "Phase 2B remains blocked: yes" in text
    assert "Execution permission granted: no" in text
    assert "Evidence quality grants execution: no" in text
    assert "live-local" in text
    for token in FORBIDDEN_SAMPLE_TOKENS:
        assert token not in text.lower(), token


def test_sample_bundle_manifest_review_passes_and_is_sanitized(tmp_path: Path) -> None:
    output = tmp_path / "sample_manifest_review.md"
    stdout = _run_bundle_review(
        "--bundle-manifest",
        str(SAMPLE_MANIFEST),
        "--output",
        str(output),
    )
    text = output.read_text(encoding="utf-8")
    assert stdout.rstrip("\n") + "\n" == text
    assert "Existing evidence quality review: run" in text
    assert "Phase 2B execution enabled: no" in text
    assert "Operator action:" in text
    for token in FORBIDDEN_SAMPLE_TOKENS:
        assert token not in text.lower(), token


def test_sample_bundle_output_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    _run_bundle_review("--artifact-dir", str(SAMPLE_DIR), "--output", str(first))
    _run_bundle_review("--artifact-dir", str(SAMPLE_DIR), "--output", str(second))
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_operator_review_packet_passes_verifier() -> None:
    result = verify_packet_text(OP_PACKET.read_text(encoding="utf-8"), source_label="op-packet")
    assert result.ok, result.findings


def test_review_packet_verifier_still_rejects_unsafe_packets() -> None:
    unsafe = OP_PACKET.read_text(encoding="utf-8") + "\nExecution permission granted: yes\n"
    result = verify_packet_text(unsafe, source_label="unsafe-op-packet")
    assert not result.ok


def test_phase2b_execution_remains_disabled_for_operator_guide() -> None:
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(_intent())
