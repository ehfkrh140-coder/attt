from __future__ import annotations

import subprocess
import sys

import pytest

from adapters.evm_readonly_client import EvmReadonlyClient
from core.errors import SafetyGuardError
from forks.evm_fork_controller import EvmForkConfig, EvmForkController, LOCAL_FORK_UNAVAILABLE
from recon.recon_engine import ReconEngine
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest


def fake_client() -> EvmReadonlyClient:
    root = "aave-root"
    return EvmReadonlyClient(
        call_results={
            (root, "getPool()"): "aave://pool",
            (root, "getPoolConfigurator()"): "aave://pool-configurator",
            (root, "getPriceOracle()"): "aave://price-oracle",
            (root, "getACLManager()"): "aave://acl-manager",
        }
    )


def test_evm_readonly_client_has_no_send_methods() -> None:
    assert not hasattr(EvmReadonlyClient, "send_transaction")
    assert not hasattr(EvmReadonlyClient, "send_raw_transaction")
    with pytest.raises(TypeError):
        EvmReadonlyClient(private_key="not-allowed")  # type: ignore[call-arg]


def test_evm_readonly_client_rejects_public_rpc() -> None:
    with pytest.raises(SafetyGuardError):
        EvmReadonlyClient(local_rpc_url="https://rpc.example.invalid", chain_id=1)


def test_evm_readonly_client_accepts_local_rpc() -> None:
    client = EvmReadonlyClient(local_rpc_url="http://127.0.0.1:8545", chain_id=31337)
    assert client.get_chain_id() == 31337


def test_verify_existing_local_fork_uses_mockable_client() -> None:
    config = EvmForkConfig("aave_v3", "ethereum", "latest", None)
    status = EvmForkController().verify_existing_local_fork(config, fake_client())
    assert status.available
    assert status.chain_id == 31337


def test_verify_existing_local_fork_reports_unavailable_without_client() -> None:
    config = EvmForkConfig("aave_v3", "ethereum", "latest", None)
    status = EvmForkController().verify_existing_local_fork(config, None)
    assert not status.available
    assert status.reason == LOCAL_FORK_UNAVAILABLE


def test_aave_v3_resolver_reads_pool_from_local_fork_client() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(protocol="aave_v3", network="ethereum", root_address="aave-root"),
        fake_client(),
    )
    assert result.target is not None
    assert any(contract["address"] == "aave://pool" for contract in result.target.in_scope_contracts)


def test_aave_v3_resolver_reads_oracle_from_local_fork_client() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(protocol="aave_v3", network="ethereum", root_address="aave-root"),
        fake_client(),
    )
    assert result.target is not None
    assert "AaveV3PriceOracle" in result.target.oracle_sources


def test_aave_v3_resolver_builds_target_spec_with_categories() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(protocol="aave_v3", network="ethereum", root_address="aave-root"),
        fake_client(),
    )
    assert result.target is not None
    categories = {contract["category"] for contract in result.target.in_scope_contracts}
    assert {"admin_config", "lending_pool", "oracle"}.issubset(categories)
    ReconEngine().run(result.target)


def test_aave_v3_resolver_partial_resolution_when_calls_missing() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(protocol="aave_v3", network="ethereum", root_address="aave-root"),
        EvmReadonlyClient(),
    )
    assert result.target is not None
    assert len(result.target.in_scope_contracts) == 1
    assert any(note.startswith("unresolved_") for note in result.notes)


def test_aave_v3_resolver_never_enables_executable_drills_in_phase_2a() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(protocol="aave_v3", network="ethereum", root_address="aave-root"),
        fake_client(),
    )
    assert result.target is not None
    assert not result.target.authorized_scope
    assert not result.target.scope_confirmed
    assert not result.scope_review.executable_drills_allowed


def test_aave_v3_resolver_requires_local_fork_client() -> None:
    result = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(protocol="aave_v3", network="ethereum", root_address="aave-root"),
        None,
    )
    assert result.target is not None
    assert "readonly_client_unavailable_partial_resolution" in result.notes


def test_aave_v3_resolver_rejects_public_rpc_client() -> None:
    with pytest.raises(SafetyGuardError):
        EvmReadonlyClient(local_rpc_url="https://rpc.example.invalid", chain_id=1)


def test_aave_v3_readonly_cli_does_not_execute_drills() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/run_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum", "--root-address", "aave-root", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Executable drills ran: no" in output


def test_aave_v3_readonly_cli_does_not_fallback_to_mock() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/run_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum", "--root-address", "aave-root", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Protocol Twin mode: evm_fork_twin" in output
    assert "mockarena_executable" not in output


def test_aave_v3_readonly_summary_lists_execution_gated() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/run_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum", "--root-address", "aave-root", "--local-rpc-url", "http://127.0.0.1:1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "LOCAL_FORK_UNAVAILABLE" in output
    assert "Execution gated: yes" in output
    assert "Read-only discovery: yes" not in output


def test_docs_mark_phase_2a_as_readonly() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/CAPABILITY_STATUS.md").read()
    assert "Phase 2A" in docs
    assert "read-only" in docs
    assert "does not execute EVM fork Red drills" in docs


def test_verify_mvp_includes_phase_2a_readonly_smoke() -> None:
    output = subprocess.run([sys.executable, "scripts/verify_mvp.py"], check=True, capture_output=True, text=True).stdout
    assert "Phase 2A.1 read-only fixture smoke: PASS" in output
