from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.safety import SafetyGuard


def record_cmd(tmp_path: Path, *extra: str) -> list[str]:
    output = tmp_path / "manual_live_fork_smoke_result.md"
    base = [
        sys.executable,
        "scripts/record_live_fork_smoke_result.py",
        "--output",
        str(output),
        "--date",
        "2026-06-10",
        "--local-fork-tool",
        "local-tool",
        "--fork-block",
        "reviewed-block",
        "--local-rpc-url",
        "http://127.0.0.1:8545",
        "--chain-id",
        "31337",
        "--root-address",
        "local-root-address-label",
        "--discovery-status",
        "partial",
        "--discovered-contracts",
        "Pool,PriceOracle",
        "--unresolved-calls",
        "ACLManager",
        "--reviewer",
        "reviewer-name",
        "--notes",
        "local-read-only-smoke",
        "--no-transaction-sent-confirmation",
        "yes",
    ]
    return base + list(extra)


def test_record_live_fork_smoke_result_rejects_public_rpc(tmp_path: Path) -> None:
    cmd = record_cmd(tmp_path)
    idx = cmd.index("--local-rpc-url") + 1
    cmd[idx] = "https://rpc.example.invalid"
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "BLOCKED_BY_SAFETY_GUARD" in result.stdout
    assert "rpc.example" not in result.stdout
    SafetyGuard().assert_safe_report(result.stdout)


def test_record_live_fork_smoke_result_rejects_private_key(tmp_path: Path) -> None:
    cmd = record_cmd(tmp_path)
    idx = cmd.index("--notes") + 1
    cmd[idx] = "private_key=unsafe"
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "BLOCKED_BY_SAFETY_GUARD" in result.stdout
    SafetyGuard().assert_safe_report(result.stdout)


def test_record_live_fork_smoke_result_rejects_raw_calldata(tmp_path: Path) -> None:
    cmd = record_cmd(tmp_path)
    idx = cmd.index("--notes") + 1
    cmd[idx] = "0x026b1d5f"
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 1
    assert "BLOCKED_BY_SAFETY_GUARD" in result.stdout
    assert "0x026b1d5f" not in result.stdout
    SafetyGuard().assert_safe_report(result.stdout)


def test_record_live_fork_smoke_result_writes_safe_markdown(tmp_path: Path) -> None:
    output = tmp_path / "manual_live_fork_smoke_result.md"
    cmd = record_cmd(tmp_path)
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    text = output.read_text()
    assert "# Manual Live Fork Smoke Result" in text
    assert "Local RPC URL: http://127.0.0.1:8545" in text
    assert "No transaction sent confirmation: yes" in text
    assert "does not enable fork execution" in text
    SafetyGuard().assert_safe_report(text)
    SafetyGuard().assert_safe_report(result.stdout)


def test_phase2b_preflight_fails_without_manual_smoke(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/phase2b_preflight.py",
            "--manual-smoke-result",
            str(tmp_path / "missing-smoke.md"),
            "--target-manifest",
            str(tmp_path / "missing-target.yaml"),
            "--dependency-graph-review",
            str(tmp_path / "missing-review.md"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Phase 2B readiness: FAIL" in result.stdout
    assert "manual live fork smoke result" in result.stdout
    SafetyGuard().assert_safe_report(result.stdout)


def test_phase2b_preflight_fails_without_target_manifest(tmp_path: Path) -> None:
    smoke = tmp_path / "manual-smoke.md"
    review = tmp_path / "review.md"
    smoke.write_text("# safe manual smoke\n")
    review.write_text("# safe dependency graph review\n")
    result = subprocess.run(
        [
            sys.executable,
            "scripts/phase2b_preflight.py",
            "--manual-smoke-result",
            str(smoke),
            "--target-manifest",
            str(tmp_path / "missing-target.yaml"),
            "--dependency-graph-review",
            str(review),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Phase 2B readiness: FAIL" in result.stdout
    assert "target manifest missing" in result.stdout
    SafetyGuard().assert_safe_report(result.stdout)


def test_phase2b_preflight_confirms_execution_still_disabled(tmp_path: Path) -> None:
    result = subprocess.run([sys.executable, "scripts/phase2b_preflight.py"], check=True, capture_output=True, text=True)
    assert "Fork execution disabled: yes" in result.stdout
    assert "Execution arena unsupported: yes" in result.stdout
    assert "Executable fork drills enabled: no" in result.stdout
    SafetyGuard().assert_safe_report(result.stdout)


def test_docs_explain_phase2b_preflight() -> None:
    text = Path("docs/PHASE_2B_PREFLIGHT.md").read_text()
    assert "Phase 2B remains blocked" in text
    assert "record_live_fork_smoke_result.py" in text
    assert "phase2b_preflight.py" in text
    assert "does not enable execution" in text
    assert "No upstream endpoint" in text


def test_verify_mvp_includes_preflight_tools() -> None:
    output = subprocess.run([sys.executable, "scripts/verify_mvp.py"], check=True, capture_output=True, text=True).stdout
    assert "Phase 2B preflight tools present: PASS" in output
    assert "Phase 2B preflight remains blocked: PASS" in output
    assert "Overall: PASS" in output
