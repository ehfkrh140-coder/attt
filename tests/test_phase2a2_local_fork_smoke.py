from __future__ import annotations

import subprocess
import sys

from core.safety import SafetyGuard


def _run(*args: str) -> str:
    return subprocess.run([sys.executable, *args], check=True, capture_output=True, text=True).stdout


def test_check_local_evm_fork_script_exists() -> None:
    assert open("scripts/check_local_evm_fork.py").read()


def test_check_local_evm_fork_unavailable_is_safe() -> None:
    output = _run("scripts/check_local_evm_fork.py", "--local-rpc-url", "http://127.0.0.1:1")
    assert "LOCAL_FORK_UNAVAILABLE" in output
    assert "Transactions enabled: no" in output
    assert "Red drills executed: no" in output
    SafetyGuard().assert_safe_report(output)


def test_check_local_evm_fork_blocks_public_rpc() -> None:
    output = _run("scripts/check_local_evm_fork.py", "--local-rpc-url", "https://rpc.example.invalid")
    assert "BLOCKED_BY_SAFETY_GUARD" in output
    SafetyGuard().assert_safe_report(output)


def test_aave_readonly_discovery_script_exists() -> None:
    assert open("scripts/aave_readonly_discovery.py").read()


def test_aave_readonly_discovery_unavailable_is_safe() -> None:
    output = _run(
        "scripts/aave_readonly_discovery.py",
        "--root-address",
        "aave-root",
        "--local-rpc-url",
        "http://127.0.0.1:1",
    )
    assert "LOCAL_FORK_UNAVAILABLE" in output
    assert "Read-only discovery: unavailable" in output
    assert "Execution gated: yes" in output
    SafetyGuard().assert_safe_report(output)


def test_aave_readonly_discovery_blocks_public_rpc() -> None:
    output = _run(
        "scripts/aave_readonly_discovery.py",
        "--root-address",
        "aave-root",
        "--local-rpc-url",
        "https://rpc.example.invalid",
    )
    assert "BLOCKED_BY_SAFETY_GUARD" in output
    assert "MockArena fallback: no" in output
    SafetyGuard().assert_safe_report(output)


def test_aave_readonly_discovery_requires_root_address() -> None:
    output = _run("scripts/aave_readonly_discovery.py", "--local-rpc-url", "http://127.0.0.1:1")
    assert "MISSING_PROTOCOL_ROOT_ADDRESS" in output
    assert "Execution gated: yes" in output
    SafetyGuard().assert_safe_report(output)


def test_aave_readonly_discovery_does_not_fallback_to_mock() -> None:
    output = _run(
        "scripts/aave_readonly_discovery.py",
        "--root-address",
        "aave-root",
        "--local-rpc-url",
        "http://127.0.0.1:1",
    )
    assert "MockArena fallback: no" in output
    assert "mockarena_executable" not in output


def test_aave_readonly_discovery_output_contains_no_raw_calldata() -> None:
    output = _run(
        "scripts/aave_readonly_discovery.py",
        "--root-address",
        "aave-root",
        "--local-rpc-url",
        "http://127.0.0.1:1",
    )
    assert "0x026b1d5f" not in output
    assert "raw_calldata" not in output.lower()
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_live_fork_unavailable_is_safe() -> None:
    output = _run(
        "scripts/run_protocol_twin.py",
        "--protocol",
        "aave_v3",
        "--network",
        "ethereum",
        "--root-address",
        "aave-root",
        "--local-rpc-url",
        "http://127.0.0.1:1",
    )
    assert "LOCAL_FORK_UNAVAILABLE" in output
    assert "Local fork reachable: no" in output
    assert "Read-only discovery: no" in output
    assert "MockArena fallback: no" in output
    SafetyGuard().assert_safe_report(output)


def test_docs_explain_live_local_fork_smoke() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/CAPABILITY_STATUS.md").read()
    assert "Phase 2A.2" in docs
    assert "Live local fork read-only smoke" in docs or "live local fork read-only smoke" in docs
    assert "LOCAL_FORK_UNAVAILABLE" in docs


def test_docs_do_not_include_public_rpc_provider_names() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/RELEASE_CHECKLIST.md").read()
    lowered = docs.lower()
    for provider in ["infura", "alchemy", "quicknode", "ankr", "blastapi", "publicnode"]:
        assert provider not in lowered
    assert "private_key" not in lowered


def test_verify_mvp_mentions_phase2a2_scripts() -> None:
    output = _run("scripts/verify_mvp.py")
    assert "Phase 2A.2 smoke scripts present: PASS" in output
    assert "Phase 2A.2 scripts stay read-only: PASS" in output
    SafetyGuard().assert_safe_report(output)
