from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.safety import SafetyGuard
from environment.bridge_twin import BridgeTwin
from environment.environment_builder import EnvironmentTwinBuilder, EnvironmentTwinSpec
from environment.fidelity import score_twin_fidelity
from environment.keeper_twin import KeeperTwin
from environment.liquidity_twin import LiquidityTwin
from environment.offchain_data_twin import OffchainDataTwin
from environment.oracle_update_twin import OracleUpdateTwin
from environment.orderflow_twin import OrderflowTwin
from redteam.executable_drill import BlindObservableBundle, BlindTxFeature
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS, ProtocolCatalog, UNSUPPORTED_PROTOCOL_TWIN

ROOT = Path(__file__).resolve().parents[1]


def _run_script(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_protocol_twin_modes_are_distinct() -> None:
    catalog = ProtocolCatalog()
    assert catalog.get("mock_lending").twin_mode == "mockarena"
    assert catalog.get("aave_v3").twin_mode == "evm_fork_twin"
    assert catalog.get("haedal").twin_mode == "sui_state_twin"


def test_mock_lending_runs_full_auto_simulation() -> None:
    result = run_auto_simulation_sync(AutoSimulationRequest(protocol="mock_lending"))
    assert result.protocol_twin_mode == "mockarena"
    assert result.executable_drills_ran
    assert result.regression_case_count >= 20
    assert result.selected_drills
    assert result.scorecard is not None


def test_aave_v3_missing_root_returns_clear_error() -> None:
    result = run_auto_simulation_sync(AutoSimulationRequest(protocol="aave_v3", network="ethereum", fork_block="latest"))
    assert result.status == MISSING_PROTOCOL_ROOT_ADDRESS
    assert MISSING_PROTOCOL_ROOT_ADDRESS in result.unsupported_components
    assert not result.executable_drills_ran


def test_aave_v3_does_not_silently_fallback_to_mock() -> None:
    result = run_auto_simulation_sync(
        AutoSimulationRequest(protocol="aave_v3", network="ethereum", root_address="aave-root", fork_block="latest", fixture_readonly=True)
    )
    assert result.protocol_twin_mode == "evm_fork_twin"
    assert result.runtime == "evm"
    assert result.status == "evm_readonly_fork_twin_execution_gated"
    assert result.protocol_twin_mode != "mockarena"
    assert not result.executable_drills_ran


def test_haedal_is_unsupported_not_faked() -> None:
    result = run_auto_simulation_sync(AutoSimulationRequest(protocol="haedal", network="sui"))
    assert result.status == UNSUPPORTED_PROTOCOL_TWIN
    assert result.protocol_twin_mode == "sui_state_twin"
    assert "sui_state_twin_adapter" in result.unsupported_components
    assert not result.executable_drills_ran


def test_environment_twin_builds_default_research_extreme_spec() -> None:
    spec = EnvironmentTwinBuilder().default_research_extreme_spec()
    assert "private_orderflow" in spec.orderflow_modes
    assert "delayed_keeper" in spec.keeper_modes
    assert "stale_oracle" in spec.oracle_modes
    assert "liquidity_shock" in spec.liquidity_modes
    assert "withdrawal_burst" in spec.user_intent_modes
    assert "gas_priority_pressure" in spec.network_modes


def test_orderflow_twin_private_mode_hides_pending_features() -> None:
    bundle = BlindObservableBundle(
        drill_id="test",
        pending_features=[
            BlindTxFeature(
                target_category="price_reference_module",
                call_shape="local_state_change",
                sender_profile="new_research_account",
                gas_profile="local_priority",
                value_bucket="zero",
                timing_pattern="clustered_pending",
                dependency_context=["oracle_path"],
                state_delta_hint="price_reference_changed",
                visibility_mode="public_local_mempool",
                local_ordering_hint="priority_cluster",
            )
        ],
        state_window={},
    )
    assert OrderflowTwin().visible_pending_features(bundle, "private_orderflow") == []


def test_keeper_twin_can_emit_delayed_keeper_condition() -> None:
    event = KeeperTwin().delayed_keeper()
    assert event.local_only
    assert event.mode == "delayed_keeper"


def test_oracle_update_twin_can_emit_stale_oracle_condition() -> None:
    event = OracleUpdateTwin().stale_oracle()
    assert event.local_only
    assert event.component == "oracle_update"


def test_liquidity_twin_can_emit_liquidity_shock_condition() -> None:
    event = LiquidityTwin().liquidity_shock()
    assert event.local_only
    assert event.mode == "liquidity_shock"


def test_bridge_twin_is_stubbed_local_only() -> None:
    twin = BridgeTwin()
    assert twin.message_delayed().local_only
    assert twin.external_calls_enabled() is False


def test_offchain_data_twin_does_not_call_external_api() -> None:
    twin = OffchainDataTwin()
    assert twin.api_unavailable().local_only
    assert twin.external_calls_enabled() is False


def test_twin_fidelity_score_penalizes_missing_external_components() -> None:
    full = EnvironmentTwinBuilder().build()
    sparse = EnvironmentTwinBuilder().build(
        EnvironmentTwinSpec(
            orderflow_modes=["public_local_mempool"],
            keeper_modes=[],
            oracle_modes=[],
            liquidity_modes=[],
            bridge_modes=[],
            offchain_modes=[],
            user_intent_modes=[],
            network_modes=[],
        )
    )
    assert score_twin_fidelity("mockarena", sparse).overall < score_twin_fidelity("mockarena", full).overall


def test_twin_fidelity_score_reports_unsupported_components() -> None:
    score = score_twin_fidelity("sui_state_twin", EnvironmentTwinBuilder().build(), ["sui_state_twin_adapter"])
    assert "sui_state_twin_adapter" in score.unsupported_components
    assert score.onchain_state_fidelity == 0.0


def test_create_protocol_twin_aave_missing_root_cli() -> None:
    output = _run_script("scripts/create_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum")
    assert MISSING_PROTOCOL_ROOT_ADDRESS in output
    assert "Protocol Twin mode: evm_fork_twin" in output
    assert "mockarena_executable" not in output
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_mock_lending_cli() -> None:
    output = _run_script("scripts/run_protocol_twin.py", "--protocol", "mock_lending")
    assert "Protocol Twin mode: mockarena" in output
    assert "Executable drills ran: yes" in output
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_aave_readonly_or_gated_cli() -> None:
    output = _run_script(
        "scripts/run_protocol_twin.py",
        "--protocol",
        "aave_v3",
        "--network",
        "ethereum",
        "--root-address",
        "aave-root",
        "--fork-block",
        "latest",
        "--local-rpc-url",
        "http://127.0.0.1:1",
    )
    assert "Protocol Twin mode: evm_fork_twin" in output
    assert "Executable drills ran: no" in output
    assert "LOCAL_FORK_UNAVAILABLE" in output or "evm_readonly_fork_twin_execution_gated" in output
    assert "mockarena_executable" not in output
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_haedal_cli() -> None:
    output = _run_script("scripts/run_protocol_twin.py", "--protocol", "haedal")
    assert UNSUPPORTED_PROTOCOL_TWIN in output
    assert "sui_state_twin" in output
    SafetyGuard().assert_safe_report(output)


def test_outputs_contain_no_public_rpc_or_secret() -> None:
    outputs = [
        _run_script("scripts/run_protocol_twin.py", "--protocol", "mock_lending"),
        _run_script("scripts/run_protocol_twin.py", "--protocol", "haedal"),
        _run_script("scripts/create_protocol_twin.py", "--protocol", "aave_v3", "--network", "ethereum"),
    ]
    forbidden = ["private_key", "send_raw_transaction", "infura", "alchemy", "quicknode", "publicnode", "https://"]
    for output in outputs:
        SafetyGuard().assert_safe_report(output)
        lowered = output.lower()
        assert all(token not in lowered for token in forbidden)


def test_docs_explain_fork_limitations_and_environment_twins() -> None:
    docs = (ROOT / "README.md").read_text() + (ROOT / "docs" / "BEGINNER_RUNBOOK.md").read_text()
    assert "does not automatically reproduce live mempool" in docs
    assert "keeper" in docs
    assert "future oracle updates" in docs
    assert "External World Twin" in docs
    assert "Twin Fidelity Score" in docs


def test_docs_do_not_claim_perfect_replication() -> None:
    docs = ((ROOT / "README.md").read_text() + (ROOT / "docs" / "BEGINNER_RUNBOOK.md").read_text()).lower()
    assert "perfect copy" not in docs
    assert "fork twin + emulated external environment" in docs
