from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from core.safety import SafetyGuard

ROOT = Path(__file__).resolve().parents[1]
UNSAFE_DOC_TOKENS = [
    "private_key",
    "raw_calldata",
    "send_raw_transaction",
    "infura",
    "alchemy",
    "quicknode",
    "publicnode",
]


def _run(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_release_checklist_exists() -> None:
    checklist = ROOT / "docs" / "RELEASE_CHECKLIST.md"
    text = checklist.read_text()
    assert checklist.exists()
    assert "pytest -q" in text
    assert "python scripts/verify_mvp.py" not in text or "Version marker" in text
    assert "Twin Fidelity Score" in text


def test_version_marker_exists() -> None:
    assert (ROOT / "VERSION").read_text().strip() == "0.1.0"


def test_version_matches_pyproject() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert (ROOT / "VERSION").read_text().strip() == pyproject["project"]["version"]


def test_verify_mvp_script_exists() -> None:
    script = ROOT / "scripts" / "verify_mvp.py"
    assert script.exists()
    assert "run_core_regression_suite_sync" in script.read_text()


def test_verify_mvp_script_runs() -> None:
    output = _run("scripts/verify_mvp.py")
    assert "MockArena MVP Verification" in output
    assert "Overall: PASS" in output


def test_verify_mvp_output_is_safe() -> None:
    output = _run("scripts/verify_mvp.py")
    SafetyGuard().assert_safe_report(output)
    lowered = output.lower()
    assert not any(token in lowered for token in UNSAFE_DOC_TOKENS)


def test_workflow_runs_verify_mvp() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text()
    assert "pip install -e \".[test]\"" in workflow
    assert "pytest -q" in workflow
    assert "python main.py" in workflow
    assert "python scripts/verify_mvp.py" in workflow


def test_readme_mentions_release_verification() -> None:
    text = (ROOT / "README.md").read_text()
    assert "MockArena MVP Release Verification" in text
    assert "python scripts/verify_mvp.py" in text
    assert "python scripts/run_protocol_twin.py --protocol mock_lending" in text


def test_beginner_runbook_explains_how_to_verify() -> None:
    text = (ROOT / "docs" / "BEGINNER_RUNBOOK.md").read_text()
    assert "How do I know it works?" in text
    assert "Overall: PASS" in text
    assert "GitHub Actions" in text


def test_capability_status_honest_about_gated_adapters() -> None:
    text = (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
    assert "EVM Fork Twin read-only/gated planning" in text
    assert "executable EVM fork Red drills | Unsupported / Not implemented" in text
    assert "Sui State Twin | Unsupported / Not implemented" in text
    assert "real Aave adapter | Unsupported / Not implemented" in text
    assert "real Haedal adapter | Unsupported / Not implemented" in text


def test_release_docs_do_not_overclaim_real_aave_or_haedal() -> None:
    docs = (
        (ROOT / "README.md").read_text()
        + (ROOT / "docs" / "BEGINNER_RUNBOOK.md").read_text()
        + (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
        + (ROOT / "docs" / "RELEASE_CHECKLIST.md").read_text()
    ).lower()
    assert "real aave adapter | unsupported" in docs
    assert "real haedal adapter | unsupported" in docs
    assert "aave v3 fork-twin onboarding path | partial" in docs
    assert "perfect copy" not in docs


def test_release_docs_contain_no_public_rpc_or_private_key() -> None:
    docs = (
        (ROOT / "README.md").read_text()
        + (ROOT / "docs" / "BEGINNER_RUNBOOK.md").read_text()
        + (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
        + (ROOT / "docs" / "RELEASE_CHECKLIST.md").read_text()
    ).lower()
    assert not any(token in docs for token in UNSAFE_DOC_TOKENS)


def test_protocol_twin_cli_outputs_safe_statuses() -> None:
    outputs = [
        _run("scripts/run_protocol_twin.py", "--protocol", "mock_lending"),
        _run("scripts/run_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum"),
        _run("scripts/run_protocol_twin.py", "--protocol", "haedal"),
    ]
    assert "Executable drills ran: yes" in outputs[0]
    assert "MISSING_PROTOCOL_ROOT_ADDRESS" in outputs[1]
    assert "UNSUPPORTED_PROTOCOL_TWIN" in outputs[2]
    for output in outputs:
        SafetyGuard().assert_safe_report(output)


def test_mockarena_mvp_release_ready() -> None:
    output = _run("scripts/verify_mvp.py")
    assert "Version: PASS" in output
    assert "Regression suite: PASS" in output
    assert "Protocol Twin mock_lending: PASS" in output
    assert "Aave V3 gated status: PASS" in output
    assert "Haedal unsupported status: PASS" in output
    assert "Overall: PASS" in output
