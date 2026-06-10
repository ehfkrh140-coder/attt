from __future__ import annotations

import subprocess
import sys

import pytest
import yaml

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_json_rpc_transport import EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient
from arenas.evm_fork_execution_arena import EvmForkExecutionArena, UNSUPPORTED_EXECUTABLE_FORK_DRILLS
from core.fork_execution_policy import ForkExecutionMode, default_fork_execution_mode
from core.safety import SafetyGuard
from redteam.local_tx_intent import LocalTxIntent
from recon.recon_engine import ReconEngine
from scripts.aave_readonly_discovery import run_discovery
from targets.aave_v3_readonly import AAVE_MAX_RESERVES_DEFAULT, AAVE_MAX_RESERVES_HARD_CAP, AaveV3CoreContracts, AaveV3ReadOnlyDiscoveryReport, AaveReserveMetadata
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest


def full_client(*, include_config: bool = True, include_price: bool = True, include_source: bool = True, reserves: int = 2) -> EvmReadonlyClient:
    root = "aave-root"
    assets = [f"aave://asset-{index}" for index in range(reserves)]
    calls = {
        (root, "aave_provider_get_pool"): "aave://pool",
        (root, "aave_provider_get_pool_configurator"): "aave://pool-configurator",
        (root, "aave_provider_get_price_oracle"): "aave://price-oracle",
        (root, "aave_provider_get_acl_manager"): "aave://acl-manager",
        ("aave://acl-manager", "aave_acl_get_pool_admin_role"): "pool-admin-role",
        ("aave://acl-manager", "aave_acl_get_risk_admin_role"): "risk-admin-role",
        ("aave://pool", "aave_pool_get_reserves_list"): assets,
    }
    for index, asset in enumerate(assets):
        calls[("aave://pool", "aave_pool_get_reserve_data", asset)] = {
            "asset": asset,
            "symbol": f"ASSET{index}",
            "a_token": f"aave://aasset-{index}",
            "stable_debt_token": f"aave://stable-debt-{index}",
            "variable_debt_token": f"aave://variable-debt-{index}",
            "decimals": 18,
            "ltv_bps": 8000,
            "liquidation_threshold_bps": 8500,
            "borrowing_enabled": True,
            "active": True,
            "frozen": False,
        }
        if include_config:
            calls[("aave://pool", "aave_pool_get_configuration", asset)] = {
                "decimals": 18,
                "ltv_bps": 8000,
                "liquidation_threshold_bps": 8500,
                "borrowing_enabled": True,
                "stable_borrow_enabled": False,
                "active": True,
                "frozen": False,
            }
        if include_price:
            calls[("aave://price-oracle", "aave_oracle_get_asset_price", asset)] = 100000000 + index
        if include_source:
            calls[("aave://price-oracle", "aave_oracle_get_source_of_asset", asset)] = f"aave://price-source-{index}"
    return EvmReadonlyClient(local_rpc_url="mock://fixture", call_results=calls)


def resolve(client: EvmReadonlyClient, *, max_reserves: int = AAVE_MAX_RESERVES_DEFAULT):
    return AaveV3Resolver(max_reserves=max_reserves).resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), client
    )


def test_aave_call_catalog_has_configuration_price_source_and_acl_labels() -> None:
    labels = set(EvmCallBuilder.safe_labels())
    assert {
        "aave_pool_get_configuration",
        "aave_oracle_get_asset_price",
        "aave_oracle_get_source_of_asset",
        "aave_acl_get_pool_admin_role",
        "aave_acl_get_risk_admin_role",
    }.issubset(labels)


def test_aave_call_catalog_has_no_execution_labels() -> None:
    forbidden = ["supply", "borrow", "repay", "withdraw", "liquidation", "approve", "transfer", "execute"]
    assert not any(token in label for label in EvmCallBuilder.safe_labels() for token in forbidden)


def test_aave_call_catalog_selectors_do_not_appear_in_reports() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    for label in EvmCallBuilder.safe_labels():
        assert EvmCallBuilder.build(label).selector not in output
    SafetyGuard().assert_safe_report(output)


def test_readonly_discovery_report_tracks_truncation() -> None:
    result = resolve(full_client(reserves=10), max_reserves=3)
    metadata = result.target.protocol_metadata["aave_v3"]  # type: ignore[union-attr]
    assert metadata["truncated"] is True
    assert metadata["max_reserves_requested"] == 3
    assert metadata["max_reserves_processed"] == 3


def test_readonly_discovery_report_tracks_watch_items() -> None:
    report = AaveV3ReadOnlyDiscoveryReport(
        core_contracts=AaveV3CoreContracts(pool_addresses_provider="aave-root"),
        reserves=[AaveReserveMetadata(asset="aave://asset", watch_items=["price_source_review"])],
        watch_items=["price_source_review"],
    )
    assert "price_source_review" in report.safe_dict()["watch_items"]


def test_readonly_discovery_report_safe_dict_contains_no_selectors() -> None:
    result = resolve(full_client())
    text = str(result.target.protocol_metadata)  # type: ignore[union-attr]
    for label in EvmCallBuilder.safe_labels():
        assert EvmCallBuilder.build(label).selector not in text
    assert "raw_calldata" not in text.lower()


def test_readonly_discovery_report_records_requested_and_processed_reserve_counts() -> None:
    result = resolve(full_client(reserves=4), max_reserves=2)
    metadata = result.target.protocol_metadata["aave_v3"]  # type: ignore[union-attr]
    assert metadata["max_reserves_requested"] == 2
    assert metadata["max_reserves_processed"] == 2
    assert metadata["reserve_count"] == 2


def test_default_max_reserves_is_8() -> None:
    resolver = AaveV3Resolver()
    assert resolver.max_reserves_requested == 8
    assert resolver.max_reserves == 8


def test_max_reserves_hard_cap_50() -> None:
    resolver = AaveV3Resolver(max_reserves=99)
    assert resolver.max_reserves == AAVE_MAX_RESERVES_HARD_CAP
    assert resolver.hard_cap_applied is True


def test_max_reserves_summary_reports_truncation() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True, max_reserves=1)
    assert "Max reserves requested: 1" in output
    assert "Max reserves processed: 1" in output
    assert "Truncated: yes" in output


def test_resolver_processes_only_max_reserves() -> None:
    result = resolve(full_client(reserves=6), max_reserves=2)
    metadata = result.target.protocol_metadata["aave_v3"]  # type: ignore[union-attr]
    assert metadata["reserve_count"] == 2
    assert metadata["truncated"] is True


def test_resolver_reads_reserve_configuration_fixture() -> None:
    result = resolve(full_client(include_config=True))
    reserve = result.target.protocol_metadata["aave_v3"]["reserves"][0]  # type: ignore[union-attr]
    assert reserve["ltv_bps"] == 8000
    assert reserve["borrowing_enabled"] is True
    assert "configuration" not in reserve["unresolved_fields"]


def test_resolver_reads_asset_price_fixture() -> None:
    result = resolve(full_client(include_price=True))
    reserve = result.target.protocol_metadata["aave_v3"]["reserves"][0]  # type: ignore[union-attr]
    assert reserve["asset_price_status"] == "available"


def test_resolver_reads_oracle_source_fixture() -> None:
    result = resolve(full_client(include_source=True))
    reserve = result.target.protocol_metadata["aave_v3"]["reserves"][0]  # type: ignore[union-attr]
    assert reserve["oracle_source_status"] == "available"
    assert "reserve_oracle_dependency" in reserve["watch_items"]


def test_missing_oracle_source_becomes_watch_item() -> None:
    result = resolve(full_client(include_source=False))
    metadata = result.target.protocol_metadata["aave_v3"]  # type: ignore[union-attr]
    assert any("oracle_source" in item for item in metadata["unresolved_reserve_fields"])
    assert "price_source_review" in metadata["watch_items"]
    assert "unresolved_reserve_fields_watch" in metadata["watch_items"]


def test_missing_configuration_becomes_watch_item() -> None:
    result = resolve(full_client(include_config=False))
    metadata = result.target.protocol_metadata["aave_v3"]  # type: ignore[union-attr]
    assert any("configuration" in item for item in metadata["unresolved_reserve_fields"])
    assert "reserve_configuration_review" in metadata["watch_items"]
    assert "unresolved_reserve_fields_watch" in metadata["watch_items"]


def test_recon_consumes_aave_watch_items() -> None:
    result = resolve(full_client(include_source=False))
    recon = ReconEngine().run(result.target)  # type: ignore[arg-type]
    assert "price_source_review" in recon.dependency_graph["watch_items"]
    assert any(h.risk_type == "price_source_review" for h in recon.risk_hypotheses)


def test_recon_generates_price_source_review_hypothesis() -> None:
    recon = ReconEngine().run(resolve(full_client()).target)  # type: ignore[arg-type]
    assert any(h.risk_type == "price_source_review" for h in recon.risk_hypotheses)


def test_recon_generates_unresolved_reserve_fields_watch() -> None:
    recon = ReconEngine().run(resolve(full_client(include_config=False)).target)  # type: ignore[arg-type]
    assert any(h.risk_type == "unresolved_reserve_fields_watch" for h in recon.risk_hypotheses)


def test_recon_adds_reserve_oracle_dependency_path() -> None:
    recon = ReconEngine().run(resolve(full_client()).target)  # type: ignore[arg-type]
    assert recon.dependency_graph["reserve_oracle_paths"]
    assert any(h.risk_type == "reserve_oracle_dependency" for h in recon.risk_hypotheses)


def test_cli_shows_max_reserves_processed_and_truncated() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/aave_readonly_discovery.py", "--root-address", "aave-root", "--fixture-readonly", "--max-reserves", "1"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Max reserves processed: 1" in output
    assert "Truncated: yes" in output
    SafetyGuard().assert_safe_report(output)


def test_cli_shows_watch_items_count() -> None:
    output = run_discovery(root_address="aave-root", fixture_readonly=True)
    assert "Watch items count:" in output
    assert "Oracle source status: available" in output
    assert "Configuration status: available" in output


def test_export_manifest_includes_watch_items_and_truncation(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    run_discovery(root_address="aave-root", fixture_readonly=True, max_reserves=1, export_target=str(export_path))
    data = yaml.safe_load(export_path.read_text())
    metadata = data["protocol_metadata"]["aave_v3"]
    assert metadata["watch_items"]
    assert metadata["truncated"] is True


def test_export_manifest_marks_readonly_only(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    run_discovery(root_address="aave-root", fixture_readonly=True, export_target=str(export_path))
    data = yaml.safe_load(export_path.read_text())
    assert data["read_only_only"] is True
    assert data["authorized_scope"] is False
    assert data["scope_confirmed"] is False
    assert data["executable_drills_allowed"] is False


def test_phase2b_still_blocked_after_completion() -> None:
    assert default_fork_execution_mode() == ForkExecutionMode.DISABLED


def test_evm_fork_execution_arena_still_raises_unsupported() -> None:
    intent = LocalTxIntent("aave-root", "sentinel", "safe", 0, "guardian", "local-normal", "phase2a4")
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(intent)


def test_no_send_sign_methods_added() -> None:
    for cls in [EvmReadonlyClient, EvmJsonRpcTransport]:
        assert not hasattr(cls, "send_transaction")
        assert not hasattr(cls, "send_raw_transaction")
        assert not hasattr(cls, "sign_transaction")
