from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from arenas.evm_fork_execution_arena import (
    UNSUPPORTED_EXECUTABLE_FORK_DRILLS,
    EvmForkExecutionArena,
)
from scripts.verify_codex_review_packet import verify_packet_text
from redteam.local_tx_intent import LocalTxIntent


REQUIRED_REVIEW_PACKET_FILES = (
    Path("docs/CODEX_PR_REVIEW_PROTOCOL.md"),
    Path("docs/reviews/README.md"),
    Path("docs/reviews/REVIEW_PACKET_TEMPLATE.md"),
    Path("docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md"),
    Path(".github/pull_request_template.md"),
    Path("scripts/verify_codex_review_packet.py"),
)

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


def _model_packet_text() -> str:
    return Path("docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md").read_text(encoding="utf-8")


def _intent() -> LocalTxIntent:
    return LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-review-packet-verification-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="phase2a6-rp-review-packet",
    )


def test_required_review_packet_files_exist_and_are_readable() -> None:
    for path in REQUIRED_REVIEW_PACKET_FILES:
        assert path.exists(), path
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert len(lines) >= 20, path
        assert max(len(line) for line in lines) <= 180, path
        bidi = [
            (line_number, hex(ord(ch)))
            for line_number, line in enumerate(lines, start=1)
            for ch in line
            if ord(ch) in BIDI_CONTROL_CODEPOINTS
        ]
        assert not bidi, (path, bidi[:5])


def test_review_packet_verifier_accepts_model_packet() -> None:
    result = verify_packet_text(_model_packet_text(), source_label="model")
    assert result.ok, result.findings


def test_review_packet_verifier_cli_accepts_model_packet() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_codex_review_packet.py",
            "--packet",
            "docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "Codex review packet verification: PASS"


def test_review_packet_verifier_github_event_mode_accepts_pr_body(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        json.dumps({"pull_request": {"body": _model_packet_text()}}),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_codex_review_packet.py",
            "--github-event",
            str(event_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "Codex review packet verification: PASS"


def test_review_packet_verifier_output_is_deterministic_for_failures() -> None:
    bad_packet = "# short packet\n"
    first = verify_packet_text(bad_packet, source_label="bad").to_text()
    second = verify_packet_text(bad_packet, source_label="bad").to_text()
    assert first == second
    assert first.startswith("Codex review packet verification: FAIL")


def test_review_packet_verifier_rejects_missing_required_sections() -> None:
    text = _model_packet_text().replace("## 4. Reviewer Focus Map", "## 4. Removed")
    result = verify_packet_text(text, source_label="missing-section")
    assert not result.ok
    assert any("Reviewer Focus Map" in finding for finding in result.findings)


@pytest.mark.parametrize(
    "unsafe_fragment",
    (
        "EXECUTION_READY",
        "Execution permission granted: yes",
        "raw_calldata: reusable-bytes",
        "raw calldata payload present",
        "transaction bundle text",
        "private_key: demo-secret",
        "https://mainnet.example.invalid",
        "\u202Ehidden-control",
        "exploit artifact: present",
    ),
)
def test_review_packet_verifier_rejects_unsafe_or_forbidden_claims(unsafe_fragment: str) -> None:
    text = _model_packet_text() + f"\n\n{unsafe_fragment}\n"
    result = verify_packet_text(text, source_label="unsafe")
    assert not result.ok


def test_review_packet_verifier_rejects_single_line_blob() -> None:
    text = " ".join(_model_packet_text().splitlines())
    result = verify_packet_text(text, source_label="single-line")
    assert not result.ok
    assert any("single-line" in finding or "too short" in finding for finding in result.findings)


def test_pull_request_template_contains_compact_review_packet_fields() -> None:
    text = Path(".github/pull_request_template.md").read_text(encoding="utf-8")
    required = (
        "## Phase / Scope",
        "## Continuity Summary",
        "## Files Changed by Category",
        "## Safety Boundary Confirmation",
        "## Phase 2B Disabled Proof",
        "## Validation Commands Run",
        "## Reviewer Focus Map",
        "## Known Gaps",
        "## Next Recommended PR",
    )
    for heading in required:
        assert heading in text


def test_workflow_runs_review_packet_verifier() -> None:
    text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")
    assert "scripts/verify_codex_review_packet.py" in text
    assert "docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md" in text


def test_phase2b_execution_remains_disabled_for_review_packet_protocol() -> None:
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(_intent())
