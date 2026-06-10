from __future__ import annotations

import subprocess
import sys

import pytest

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_json_rpc_transport import EvmJsonRpcError, EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient
from core.errors import SafetyGuardError
from core.safety import SafetyGuard
from reports.report_writer import write_protocol_twin_summary
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest


def requester_for(results: dict[str, object]):
    calls: list[str] = []

    def requester(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        method = str(payload["method"])
        calls.append(method)
        if method == "eth_call":
            params = payload["params"]
            assert isinstance(params, list)
            call_object = params[0]
            assert isinstance(call_object, dict)
            results["last_call_data"] = call_object["data"]
        if method not in results:
            raise OSError("missing local fork fixture")
        value = results[method]
        if isinstance(value, Exception):
            raise value
        return {"result": value}

    requester.calls = calls  # type: ignore[attr-defined]
    return requester


def abi_address(hex_tail: str) -> str:
    return "0x" + "0" * 24 + hex_tail.removeprefix("0x").lower().rjust(40, "0")


def test_evm_json_rpc_transport_allows_readonly_methods() -> None:
    requester = requester_for({"eth_chainId": "0x7a69", "web3_clientVersion": "local-test"})
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester)
    assert transport.call("eth_chainId", []) == "0x7a69"
    assert transport.call("web3_clientVersion", []) == "local-test"


def test_evm_json_rpc_transport_blocks_send_methods() -> None:
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester_for({}))
    for method in ["eth_sendTransaction", "eth_sendRawTransaction", "personal_sign", "wallet_switchEthereumChain", "anvil_setBalance"]:
        with pytest.raises(SafetyGuardError):
            transport.call(method, [])


def test_evm_json_rpc_transport_rejects_public_rpc_url() -> None:
    with pytest.raises(SafetyGuardError):
        EvmJsonRpcTransport("https://rpc.example.invalid")


def test_evm_readonly_client_transport_get_chain_id() -> None:
    client = EvmReadonlyClient(transport=EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester_for({"eth_chainId": "0x7a69"})))
    assert client.get_chain_id() == 31337


def test_evm_readonly_client_transport_get_code() -> None:
    client = EvmReadonlyClient(transport=EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester_for({"eth_getCode": "0x6000"})))
    assert client.get_code("0x0000000000000000000000000000000000000001") == "0x6000"


def test_evm_readonly_client_transport_eth_call() -> None:
    requester = requester_for({"eth_call": abi_address("0x00000000000000000000000000000000000000aa")})
    client = EvmReadonlyClient(transport=EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester))
    result = client.eth_call("0x0000000000000000000000000000000000000001", EvmCallBuilder.aave_provider_get_pool())
    assert str(result).endswith("aa")
    assert requester.calls == ["eth_call"]  # type: ignore[attr-defined]


def test_evm_readonly_client_has_no_send_methods_phase2a1() -> None:
    assert not hasattr(EvmReadonlyClient, "send_transaction")
    assert not hasattr(EvmReadonlyClient, "send_raw_transaction")


def test_evm_call_builder_uses_safe_labels() -> None:
    call = EvmCallBuilder.aave_provider_get_pool()
    assert call.safe_label == "aave_provider_get_pool"
    assert call.selector.startswith("0x")
    assert "getPool" not in call.safe_label


def test_reports_do_not_expose_raw_calldata_from_call_builder() -> None:
    result = run_auto_simulation_sync(
        AutoSimulationRequest(protocol="aave_v3", network="ethereum", root_address="aave-root", fixture_readonly=True)
    )
    summary = write_protocol_twin_summary(result)
    assert EvmCallBuilder.aave_provider_get_pool().selector not in summary
    SafetyGuard().assert_safe_report(summary)


def test_aave_resolver_uses_safe_named_calls() -> None:
    root = "0x0000000000000000000000000000000000000001"
    client = EvmReadonlyClient(
        call_results={
            (root.lower(), "aave_provider_get_pool"): "aave://pool",
            (root.lower(), "aave_provider_get_price_oracle"): "aave://price-oracle",
        }
    )
    result = AaveV3Resolver().resolve(ProtocolResolutionRequest("aave_v3", "ethereum", root_address=root), client)
    assert result.target is not None
    addresses = {contract["address"] for contract in result.target.in_scope_contracts}
    assert "aave://pool" in addresses
    assert "aave://price-oracle" in addresses


def test_aave_resolver_handles_local_fork_unavailable() -> None:
    transport = EvmJsonRpcTransport("http://127.0.0.1:8545", requester=requester_for({"eth_chainId": OSError("offline")}))
    client = EvmReadonlyClient(transport=transport)
    with pytest.raises(EvmJsonRpcError):
        client.get_chain_id()


def test_run_protocol_twin_aave_local_fork_unavailable_is_safe() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/run_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum", "--root-address", "aave-root", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "LOCAL_FORK_UNAVAILABLE" in output
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_aave_does_not_fallback_to_mock() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/run_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum", "--root-address", "aave-root", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Protocol Twin mode: evm_fork_twin" in output
    assert "mockarena_executable" not in output


def test_verify_mvp_phase2a1_fixture_smoke() -> None:
    output = subprocess.run([sys.executable, "scripts/verify_mvp.py"], check=True, capture_output=True, text=True).stdout
    assert "Phase 2A.1 read-only fixture smoke: PASS" in output


def test_docs_mark_phase2a1_readonly_transport() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/CAPABILITY_STATUS.md").read()
    assert "Phase 2A.1" in docs
    assert "read-only transport" in docs or "read-only discovery" in docs
    assert "LOCAL_FORK_UNAVAILABLE" in docs


def test_docs_do_not_include_public_rpc_url_or_private_key() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/RELEASE_CHECKLIST.md").read()
    lowered = docs.lower()
    assert "infura" not in lowered
    assert "alchemy" not in lowered
    assert "quicknode" not in lowered
    assert "private_key" not in lowered
