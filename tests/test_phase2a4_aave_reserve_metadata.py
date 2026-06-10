from __future__ import annotations

import subprocess
import sys

import yaml

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_readonly_client import EvmReadonlyClient
from core.safety import SafetyGuard
from recon.recon_engine import ReconEngine
from scripts.aave_readonly_discovery import run_discovery
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest


def word(value: int) -> str:
    return hex(value).removeprefix("0x").rjust(64, "0")


def abi_address(address: str) -> str:
    return address.removeprefix("0x").lower().rjust(64, "0")


def abi_address_array(addresses: list[str]) -> str:
    return "0x" + word(32) + word(len(addresses)) + "".join(abi_address(address) for address in addresses)


def abi_reserve_data(*, a_token: str, stable_debt: str, variable_debt: str, strategy: str) -> str:
    config = 8000 | (8500 << 16) | (18 << 48) | (1 << 56) | (1 << 58)
    words = [word(config)] + [word(0)] * 7 + [abi_address(a_token), abi_address(stable_debt), abi_address(variable_debt), abi_address(strategy)]
    return "0x" + "".join(words)


def reserve_client(*, include_reserve_data: bool = True, reserve_count: int = 2) -> EvmReadonlyClient:
    root = "aave-root"
    assets = [f"aave://asset-{index}" for index in range(reserve_count)]
    call_results = {
        (root, "aave_provider_get_pool"): "aave://pool",
        (root, "aave_provider_get_pool_configurator"): "aave://pool-configurator",
        (root, "aave_provider_get_price_oracle"): "aave://price-oracle",
        (root, "aave_provider_get_acl_manager"): "aave://acl-manager",
        ("aave://pool", "aave_pool_get_reserves_list"): assets,
    }
    if include_reserve_data:
        for index, asset in enumerate(assets):
            call_results[("aave://pool", "aave_pool_get_reserve_data", asset)] = {
                "asset": asset,
                "symbol": f"ASSET{index}",
                "a_token": f"aave://aasset-{index}",
                "stable_debt_token": f"aave://stable-debt-{index}",
                "variable_debt_token": f"aave://variable-debt-{index}",
                "interest_rate_strategy": f"aave://rate-strategy-{index}",
                "decimals": 18,
                "ltv_bps": 8000,
                "liquidation_threshold_bps": 8500,
                "borrowing_enabled": True,
                "active": True,
                "frozen": False,
            }
    return EvmReadonlyClient(local_rpc_url="mock://fixture", call_results=call_results)


def resolve_with(client: EvmReadonlyClient, *, max_reserves: int = 20):
    return AaveV3Resolver(max_reserves=max_reserves).resolve(
        ProtocolResolutionRequest("aave_v3", "ethereum", root_address="aave-root"), client
    )


def test_aave_resolver_discovers_fixture_reserve_metadata_for_recon() -> None:
    result = resolve_with(reserve_client())
    assert result.target is not None
    metadata = result.target.protocol_metadata["aave_v3"]
    assert metadata["reserve_discovery_status"] == "fully_discovered"
    assert metadata["reserve_count"] == 2
    assert {reserve["symbol"] for reserve in metadata["reserves"]} == {"ASSET0", "ASSET1"}
    categories = {contract["category"] for contract in result.target.in_scope_contracts}
    assert {"reserve_asset", "a_token", "variable_debt_token", "stable_debt_token"}.issubset(categories)
    recon = ReconEngine().run(result.target)
    assert recon.dependency_graph["reserve_paths"]
    assert any(hypothesis.risk_type == "reserve_configuration" for hypothesis in recon.risk_hypotheses)


def test_aave_resolver_partial_reserve_decode_unavailable() -> None:
    result = resolve_with(reserve_client(include_reserve_data=False))
    assert result.target is not None
    metadata = result.target.protocol_metadata["aave_v3"]
    assert metadata["reserve_discovery_status"] == "partially_discovered"
    assert all(reserve["discovery_status"] == "decode_unavailable" for reserve in metadata["reserves"])
    assert "reserve_data_decode_unavailable" in result.notes


def test_aave_resolver_reserve_list_unavailable_is_honest() -> None:
    client = EvmReadonlyClient(
        local_rpc_url="mock://fixture",
        call_results={
            ("aave-root", "aave_provider_get_pool"): "aave://pool",
            ("aave-root", "aave_provider_get_pool_configurator"): "aave://pool-configurator",
            ("aave-root", "aave_provider_get_price_oracle"): "aave://price-oracle",
            ("aave-root", "aave_provider_get_acl_manager"): "aave://acl-manager",
        },
    )
    result = resolve_with(client)
    assert result.target is not None
    assert result.discovery_status == "fully_discovered"
    assert result.target.protocol_metadata["aave_v3"]["reserve_discovery_status"] == "unavailable"
    assert "reserve_list_unresolved" in result.notes


def test_aave_resolver_reserve_cap_limits_large_fixture() -> None:
    result = resolve_with(reserve_client(reserve_count=5), max_reserves=2)
    assert result.target is not None
    metadata = result.target.protocol_metadata["aave_v3"]
    assert metadata["reserve_count"] == 2
    assert metadata["reserve_cap"] == 2
    assert "reserve_discovery_limited_to_2" in result.notes


def test_aave_resolver_decodes_abi_reserve_list_and_data() -> None:
    root = "aave-root"
    pool = "0x00000000000000000000000000000000000000aa"
    asset = "0x00000000000000000000000000000000000000bb"
    client = EvmReadonlyClient(
        local_rpc_url="mock://fixture",
        call_results={
            (root, "aave_provider_get_pool"): pool,
            (root, "aave_provider_get_pool_configurator"): "aave://pool-configurator",
            (root, "aave_provider_get_price_oracle"): "aave://price-oracle",
            (root, "aave_provider_get_acl_manager"): "aave://acl-manager",
            (pool, "aave_pool_get_reserves_list"): abi_address_array([asset]),
            (pool, "aave_pool_get_reserve_data", asset): abi_reserve_data(
                a_token="0x00000000000000000000000000000000000000cc",
                stable_debt="0x00000000000000000000000000000000000000dd",
                variable_debt="0x00000000000000000000000000000000000000ee",
                strategy="0x00000000000000000000000000000000000000ff",
            ),
        },
    )
    result = resolve_with(client)
    assert result.target is not None
    reserve = result.target.protocol_metadata["aave_v3"]["reserves"][0]
    assert reserve["discovery_status"] == "decoded"
    assert reserve["decimals"] == 18
    assert reserve["borrowing_enabled"] is True
    assert reserve["a_token"].endswith("cc")


def test_aave_readonly_cli_reports_reserve_summary() -> None:
    output = subprocess.run(
        [sys.executable, "scripts/aave_readonly_discovery.py", "--root-address", "aave-root", "--fixture-readonly"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Reserve discovery: fully_discovered" in output
    assert "Reserve count: 2" in output
    assert "Reserve symbols: USDC, WETH" in output
    assert EvmCallBuilder.aave_pool_get_reserves_list().selector not in output
    SafetyGuard().assert_safe_report(output)


def test_run_protocol_twin_reports_reserve_recon_summary() -> None:
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
    assert "Reserve discovery: fully_discovered" in output
    assert "Discovered reserves: USDC, WETH" in output
    assert "ExecutableLiquidationStressDrill" in output
    SafetyGuard().assert_safe_report(output)


def test_exported_target_manifest_contains_reserve_metadata_without_selectors(tmp_path) -> None:
    export_path = tmp_path / "aave_v3_readonly.yaml"
    run_discovery(root_address="aave-root", fixture_readonly=True, export_target=str(export_path))
    data = yaml.safe_load(export_path.read_text())
    assert data["protocol_metadata"]["aave_v3"]["reserve_count"] == 2
    manifest = export_path.read_text()
    for call in [EvmCallBuilder.aave_pool_get_reserves_list(), EvmCallBuilder.aave_pool_get_reserve_data("aave://usdc")]:
        assert call.selector not in manifest
    assert "raw_calldata" not in manifest.lower()
