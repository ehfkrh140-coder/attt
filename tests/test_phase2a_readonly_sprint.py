from __future__ import annotations

import inspect
import subprocess
import sys

import pytest
import yaml

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_json_rpc_transport import EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient
from core.errors import SafetyGuardError
from core.safety import SafetyGuard
from reports.report_writer import write_protocol_twin_summary
from scripts.aave_readonly_discovery import run_discovery
from scripts.check_local_evm_fork import run_check
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest


class MockTransport:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def call(self, method: str, params: list[object] | None = None) -> object:
        self.calls.append(method)
        if method not in self.responses:
            raise OSError("missing fixture response")
        value = self.responses[method]
        if isinstance(value, Exception):
            raise value
        return value


def abi_address(short: str) -> str:
    return "0x" + "0" * 24 + short.removeprefix("0x").rjust(40, "0")


def fake_client(partial: bool = False) -> EvmReadonlyClient:
    root = "aave-root"
    calls = {
        (root, "aave_provider_get_pool"): "aave://pool",
        (root, "aave_provider_get_pool_configurator"): "aave://pool-configurator",
        (root, "aave_provider_get_price_oracle"): "aave://price-oracle",
        (root, "aave_provider_get_acl_manager"): "aave://acl-manager",
    }
    if partial:
        calls.pop((root, "aave_provider_get_acl_manager"))
    return EvmReadonlyClient(call_results=calls)


def test_check_local_evm_fork_success_with_mock_transport() -> None:
    output = run_check(
        "http://127.0.0.1:8545",
        transport_factory=lambda _url: MockTransport({"eth_chainId": "0x7a69", "web3_clientVersion": "local"}),  # type: ignore[arg-type]
    )
    assert "Local fork reachable: yes" in output
    assert "Safety status: PASS" in output
    assert "Transactions enabled: no" in output
    SafetyGuard().assert_safe_report(output)


def test_check_local_evm_fork_unavailable_no_traceback() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/check_local_evm_fork.py", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "LOCAL_FORK_UNAVAILABLE" in output
    assert "Traceback" not in output


def test_check_local_evm_fork_output_is_safe() -> None:
    SafetyGuard().assert_safe_report(run_check("http://127.0.0.1:1"))


def test_aave_resolver_discovery_status_full() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), fake_client()
    )
    assert result.discovery_status == "fully_discovered"


def test_aave_resolver_discovery_status_partial() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), fake_client(partial=True)
    )
    assert result.discovery_status == "partially_discovered"


def test_aave_resolver_discovery_status_unavailable() -> None:
    result = AaveV3Resolver().resolve(ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), None)
    assert result.discovery_status == "unavailable"


def test_aave_resolver_normalizes_abi_address() -> None:
    address = abi_address("0x1234")
    client = EvmReadonlyClient(call_results={("aave-root", "aave_provider_get_pool"): address})
    result = AaveV3Resolver().resolve(ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), client)
    assert result.target is not None
    assert any(contract["address"].endswith("1234") for contract in result.target.in_scope_contracts)


def test_aave_resolver_notes_unresolved_calls() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), fake_client(partial=True)
    )
    assert "unresolved_ACLManager" in result.notes
    assert "discovery_status_partially_discovered" in result.notes


def test_aave_resolver_target_spec_has_expected_categories() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), fake_client()
    )
    assert result.target is not None
    categories = {contract["category"] for contract in result.target.in_scope_contracts}
    assert {"admin_config", "lending_pool", "oracle"}.issubset(categories)


def test_aave_resolver_never_enables_scope_or_execution() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), fake_client()
    )
    assert result.target is not None
    assert not result.target.scope_confirmed
    assert not result.target.authorized_scope
    assert not result.scope_review.executable_drills_allowed


def test_aave_readonly_discovery_can_export_safe_target_manifest(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    output = subprocess.run(
        [
            sys.executable,
            "scripts/aave_readonly_discovery.py",
            "--root-address",
            "aave-root",
            "--fixture-readonly",
            "--export-target",
            str(export_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert export_path.exists()
    assert "Read-only discovery: full" in output
    SafetyGuard().assert_safe_report(output)


def test_exported_target_manifest_scope_unconfirmed(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    run_discovery(root_address="aave-root", fixture_readonly=True, export_target=str(export_path))
    data = yaml.safe_load(export_path.read_text())
    assert data["authorized_scope"] is False
    assert data["scope_confirmed"] is False
    assert data["executable_drills_allowed"] is False


def test_exported_target_manifest_contains_no_secrets_or_public_rpc(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    run_discovery(root_address="aave-root", fixture_readonly=True, export_target=str(export_path))
    text = export_path.read_text().lower()
    for token in ["private_key", "mnemonic", "infura", "alchemy", "quicknode", "raw_calldata"]:
        assert token not in text


def test_run_protocol_twin_aave_output_contains_recon_summary() -> None:
    output = subprocess.run(
        [
            sys.executable,
            "scripts/run_protocol_twin.py",
            "--protocol",
            "aave_v3",
            "--network",
            "ethereum",
            "--root-address",
            "aave-root",
            "--fixture-readonly",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Read-only discovery: full" in output
    assert "Recon risk hypotheses count:" in output
    assert "Selected drill recommendations:" in output
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_aave_output_contains_no_mock_fallback() -> None:
    result = run_auto_simulation_sync(
        AutoSimulationRequest(protocol="aave_v3", network="ethereum", root_address="aave-root", fixture_readonly=True)
    )
    summary = write_protocol_twin_summary(result)
    assert "mockarena_executable" not in summary
    assert not result.executable_drills_ran


def test_phase2a_no_send_methods_in_transport_or_client() -> None:
    assert not hasattr(EvmJsonRpcTransport, "send_transaction")
    assert not hasattr(EvmJsonRpcTransport, "send_raw_transaction")
    assert not hasattr(EvmReadonlyClient, "send_transaction")
    assert not hasattr(EvmReadonlyClient, "send_raw_transaction")


def test_phase2a_forbidden_rpc_methods_blocked() -> None:
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=lambda *_args: {"result": "ok"})
    for method in ["eth_sendTransaction", "eth_sendRawTransaction", "eth_sign", "personal_sign", "txpool_content"]:
        with pytest.raises(SafetyGuardError):
            transport.call(method, [])


def test_phase2a_public_rpc_rejected_before_request() -> None:
    called = False

    def requester(*_args):
        nonlocal called
        called = True
        return {"result": "0x1"}

    with pytest.raises(SafetyGuardError):
        EvmJsonRpcTransport("https://rpc.example.invalid", requester=requester)
    assert called is False


def test_phase2a_no_private_key_argument_anywhere_in_evm_adapter() -> None:
    assert "private_key" not in str(inspect.signature(EvmReadonlyClient))
    assert "private_key" not in str(inspect.signature(EvmJsonRpcTransport))


def test_phase2a_reports_do_not_contain_raw_calldata_or_selectors() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    assert EvmCallBuilder.aave_provider_get_pool().selector not in output
    assert "raw_calldata" not in output.lower()
    SafetyGuard().assert_safe_report(output)


def test_phase2a_aave_cli_does_not_execute_drills() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    assert "Executable drills ran: no" in output
    assert "Execution gated: yes" in output


def test_phase2a_aave_cli_does_not_use_mockarena_as_fallback() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    assert "MockArena fallback: no" in output
    assert "mockarena_executable" not in output


def test_phase2a_verify_mvp_still_passes() -> None:
    output = subprocess.run([sys.executable, "scripts/verify_mvp.py"], check=True, capture_output=True, text=True).stdout
    assert "Overall: PASS" in output


def test_docs_explain_phase2a_readonly_workflow() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read()
    assert "Phase 2A Read-only Local Fork Workflow" in docs
    assert "check_local_evm_fork.py" in docs
    assert "aave_readonly_discovery.py" in docs


def test_docs_do_not_include_public_rpc_or_provider_names() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/RELEASE_CHECKLIST.md").read()
    lowered = docs.lower()
    for token in ["infura", "alchemy", "quicknode", "ankr", "blastapi", "publicnode", "private_key"]:
        assert token not in lowered


def test_docs_say_no_transactions_and_no_red_drills() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read()
    assert "No transactions are sent" in docs
    assert "Red drills are not executed on Aave" in docs


def test_docs_say_phase2b_is_future_work() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read()
    assert "Phase 2B" in docs
    assert "future" in docs.lower()
