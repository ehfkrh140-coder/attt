from __future__ import annotations

import subprocess
import sys

import pytest

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_json_rpc_transport import FORBIDDEN_RPC_PREFIXES, READONLY_RPC_METHODS, EvmJsonRpcError, EvmJsonRpcTransport
from core.errors import SafetyGuardError
from core.safety import SafetyGuard
from scripts.aave_readonly_discovery import run_discovery


def test_phase2a_depth_audit_doc_exists() -> None:
    assert open("docs/PHASE_2A_DEPTH_AUDIT.md").read()


def test_phase2a_depth_audit_lists_fixture_vs_live_limits() -> None:
    text = open("docs/PHASE_2A_DEPTH_AUDIT.md").read()
    assert "Fixture-backed CI tests" in text
    assert "Optional live local fork manual commands" in text
    assert "What has been proven" in text
    assert "What has not been proven" in text
    assert "Real Anvil/Hardhat fork connectivity" in text


def test_manual_live_fork_smoke_script_exists() -> None:
    assert open("scripts/manual_live_fork_smoke.py").read()


def test_manual_live_fork_smoke_not_run_in_ci() -> None:
    workflow = open(".github/workflows/test.yml").read()
    assert "manual_live_fork_smoke.py" not in workflow
    help_output = subprocess.run(
        [sys.executable, "scripts/manual_live_fork_smoke.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Optional manual" in help_output
    assert "Not used" in help_output and "by CI" in help_output


def test_manual_live_fork_smoke_contains_no_public_rpc_or_private_key() -> None:
    text = open("scripts/manual_live_fork_smoke.py").read().lower()
    for token in ["infura", "alchemy", "quicknode", "ankr", "blastapi", "publicnode", "private_key"]:
        assert token not in text


def test_manual_live_fork_smoke_does_not_send_transactions() -> None:
    text = open("scripts/manual_live_fork_smoke.py").read()
    assert "send_transaction" not in text
    assert "send_raw_transaction" not in text
    assert "eth_sendTransaction" not in text
    assert "eth_sendRawTransaction" not in text


def test_transport_forbidden_method_prefixes_blocked() -> None:
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=lambda *_args: {"result": "ok"})
    for prefix in FORBIDDEN_RPC_PREFIXES:
        with pytest.raises(SafetyGuardError):
            transport.call(f"{prefix}example", [])


def test_transport_unknown_method_blocked() -> None:
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=lambda *_args: {"result": "ok"})
    with pytest.raises(SafetyGuardError):
        transport.call("eth_getLogs", [])


def test_transport_does_not_log_payload_on_error() -> None:
    selector = EvmCallBuilder.aave_provider_get_pool().selector

    def requester(*_args):
        raise OSError(f"boom payload {selector}")

    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester)
    with pytest.raises(EvmJsonRpcError) as exc:
        transport.call("eth_call", [{"to": "aave-root", "data": selector}, "latest"])
    assert str(exc.value) == "LOCAL_FORK_UNAVAILABLE"
    assert selector not in str(exc.value)


def test_transport_error_message_contains_no_raw_calldata() -> None:
    selector = EvmCallBuilder.aave_provider_get_pool().selector
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=lambda *_args: {"error": {"message": selector}})
    with pytest.raises(EvmJsonRpcError) as exc:
        transport.call("eth_call", [{"to": "aave-root", "data": selector}, "latest"])
    assert selector not in str(exc.value)
    SafetyGuard().assert_safe_report(str(exc.value))


def test_transport_timeout_returns_safe_local_fork_unavailable() -> None:
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=lambda *_args: (_ for _ in ()).throw(TimeoutError("slow")))
    with pytest.raises(EvmJsonRpcError) as exc:
        transport.call("eth_chainId", [])
    assert str(exc.value) == "LOCAL_FORK_UNAVAILABLE"


def test_transport_allows_only_declared_read_methods() -> None:
    assert READONLY_RPC_METHODS == {
        "eth_chainId",
        "eth_getCode",
        "eth_call",
        "eth_getStorageAt",
        "eth_getBalance",
        "net_version",
        "web3_clientVersion",
    }


def test_no_report_contains_aave_selectors() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    for call in [
        EvmCallBuilder.aave_provider_get_pool(),
        EvmCallBuilder.aave_provider_get_pool_configurator(),
        EvmCallBuilder.aave_provider_get_price_oracle(),
        EvmCallBuilder.aave_provider_get_acl_manager(),
    ]:
        assert call.selector not in output
    SafetyGuard().assert_safe_report(output)


def test_aave_discovery_summary_contains_safe_labels_only() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    assert "Selected drill recommendations" in output
    assert "raw_calldata" not in output.lower()
    assert "eth_call" not in output


def test_exported_manifest_does_not_store_raw_call_selectors(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    run_discovery(root_address="aave-root", fixture_readonly=True, export_target=str(export_path))
    manifest = export_path.read_text()
    for call in [
        EvmCallBuilder.aave_provider_get_pool(),
        EvmCallBuilder.aave_provider_get_pool_configurator(),
        EvmCallBuilder.aave_provider_get_price_oracle(),
        EvmCallBuilder.aave_provider_get_acl_manager(),
    ]:
        assert call.selector not in manifest


def test_logs_do_not_include_raw_rpc_payload() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/aave_readonly_discovery.py", "--root-address", "aave-root", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "jsonrpc" not in output.lower()
    assert "params" not in output.lower()
    SafetyGuard().assert_safe_report(output)


def test_phase2b_readiness_checklist_exists() -> None:
    assert open("docs/PHASE_2B_READINESS_CHECKLIST.md").read()


def test_phase2b_checklist_blocks_execution_until_live_readonly_verified() -> None:
    text = open("docs/PHASE_2B_READINESS_CHECKLIST.md").read()
    assert "Live local fork manual smoke has been run by the user" in text
    assert "Local fork read-only discovery works against a real fork" in text
    assert "No private keys" in text
    assert "stay in read-only Phase 2A" in text


def test_verify_mvp_includes_depth_audit_checks() -> None:
    output = subprocess.run([sys.executable, "scripts/verify_mvp.py"], check=True, capture_output=True, text=True).stdout
    assert "Phase 2A QA audit docs: PASS" in output
    assert "Overall: PASS" in output


def test_docs_do_not_overclaim_real_aave_support() -> None:
    docs = open("README.md").read() + open("docs/PHASE_2A_DEPTH_AUDIT.md").read() + open("docs/CAPABILITY_STATUS.md").read()
    lowered = docs.lower()
    assert "real aave defense bot" in lowered
    assert "not executable fork drill support" in lowered or "not implemented" in lowered
    assert "phase 2b is future" in lowered or "future work" in lowered
