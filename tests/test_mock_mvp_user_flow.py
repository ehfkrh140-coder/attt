from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.safety import SafetyGuard
from eval.regression_suite import CORE_REGRESSION_DRILLS, CORE_REGRESSION_MODES

ROOT = Path(__file__).resolve().parents[1]
UNSAFE_OUTPUT_TOKENS = [
    "raw_calldata",
    "calldata:",
    "private_key",
    "mnemonic",
    "seed phrase",
    "send_raw_transaction",
    "sign_transaction",
    "account.sign_transaction",
    "http://",
    "https://",
    "infura",
    "alchemy",
    "quicknode",
    "ankr",
    "blastapi",
    "publicnode",
]


def _main_output() -> str:
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_beginner_runbook_exists() -> None:
    runbook = ROOT / "docs" / "BEGINNER_RUNBOOK.md"
    text = runbook.read_text()
    assert runbook.exists()
    assert "pip install -e \".[test]\"" in text
    assert "pytest -q" in text
    assert "python main.py" in text
    assert "GitHub" in text


def test_capability_status_exists() -> None:
    status = ROOT / "docs" / "CAPABILITY_STATUS.md"
    text = status.read_text()
    assert status.exists()
    assert "Capability | Status | Notes" in text
    assert "MockArena executable drills" in text
    assert "Scorecards" in text


def test_main_outputs_beginner_summary() -> None:
    output = _main_output()
    assert "DeFi Defense Simulation Summary" in output
    assert "Recon score:" in output
    assert "Red drill score:" in output
    assert "Blue defense score:" in output
    assert "Safety score:" in output
    assert "Evaluation quality score:" in output
    assert "Regression cases:" in output
    assert "Modes tested:" in output


def test_main_output_mentions_mockarena_only() -> None:
    output = _main_output()
    assert "MockArena only" in output
    assert "contained mock runtime" in output


def test_main_output_mentions_evm_sui_gated() -> None:
    output = _main_output()
    assert "EVM/Sui adapters are gated" in output
    assert "not implemented yet" in output


def test_main_output_contains_no_unsafe_artifacts() -> None:
    output = _main_output()
    SafetyGuard().assert_safe_report(output)
    lowered = output.lower()
    for token in UNSAFE_OUTPUT_TOKENS:
        assert token not in lowered


def test_examples_are_mockarena_only() -> None:
    for relative in [
        "examples/run_mock_mvp.py",
        "examples/run_regression_suite.py",
        "examples/print_beginner_summary.py",
    ]:
        text = (ROOT / relative).read_text().lower()
        assert "run_core_regression_suite_sync" in text
        assert "evmforkarena" not in text
        assert "suilocalnetarena" not in text
        assert "http://" not in text
        assert "https://" not in text
        assert "private_key" not in text


def test_github_actions_workflow_safe() -> None:
    workflow = ROOT / ".github" / "workflows" / "test.yml"
    text = workflow.read_text().lower()
    assert workflow.exists()
    assert "pytest -q" in text
    assert "python main.py" in text
    assert "secrets" not in text
    assert "private_key" not in text
    assert "mainnet" not in text
    for provider in ["infura", "alchemy", "quicknode", "ankr", "blastapi", "publicnode"]:
        assert provider not in text


def test_capability_status_is_honest_about_unsupported_adapters() -> None:
    text = (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
    assert "EVM Fork adapter | Gated / Not implemented" in text
    assert "Sui Localnet adapter | Gated / Not implemented" in text
    assert "Public network execution | Not supported" in text
    assert "Real private keys | Not supported" in text


def test_regression_suite_exposes_core_case_count() -> None:
    expected_cases = len(CORE_REGRESSION_DRILLS) * len(CORE_REGRESSION_MODES)
    assert expected_cases >= 20
    output = _main_output()
    assert f"Regression cases: {expected_cases}" in output
    for mode in CORE_REGRESSION_MODES:
        assert mode in output
