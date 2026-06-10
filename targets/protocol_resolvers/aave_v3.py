from __future__ import annotations

from typing import Any

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_readonly_client import EvmReadonlyClient
from targets.aave_v3_readonly import AaveReserveMetadata, AaveV3ReadOnlyMetadata
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS, ProtocolCatalog
from targets.protocol_resolvers.base import ProtocolResolutionRequest, ProtocolResolutionResult, ScopeReviewReport
from targets.target_schema import TargetProtocolSpec

AAVE_PROVIDER_CALLS = {
    "Pool": EvmCallBuilder.aave_provider_get_pool,
    "PoolConfigurator": EvmCallBuilder.aave_provider_get_pool_configurator,
    "PriceOracle": EvmCallBuilder.aave_provider_get_price_oracle,
    "ACLManager": EvmCallBuilder.aave_provider_get_acl_manager,
}

AAVE_CATEGORIES = {
    "Pool": "lending_pool",
    "PoolConfigurator": "admin_config",
    "PriceOracle": "oracle",
    "ACLManager": "admin_config",
}


class AaveV3Resolver:
    def __init__(self, catalog: ProtocolCatalog | None = None, *, max_reserves: int = 20) -> None:
        self.catalog = catalog or ProtocolCatalog()
        self.max_reserves = max_reserves

    def _root_for(self, request: ProtocolResolutionRequest) -> str | None:
        if request.root_address:
            return request.root_address
        return self.catalog.get("aave_v3").known_roots.get(request.network)

    def scope_review(self, request: ProtocolResolutionRequest) -> ScopeReviewReport:
        root = self._root_for(request)
        return ScopeReviewReport(
            protocol_name="aave_v3",
            twin_mode="evm_fork_twin",
            candidate_contracts=[] if root is None else [{"name": "PoolAddressesProvider", "address": root}],
            scope_confirmed=False,
            executable_drills_allowed=False,
            status="supported_readonly_or_gated_execution",
            reason=None if root else MISSING_PROTOCOL_ROOT_ADDRESS,
        )

    def _normalize_address(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None
        if value in {"", "0x"}:
            return None
        if value.startswith("0x") and len(value) == 66:
            candidate = "0x" + value[-40:]
            if int(candidate, 16) == 0:
                return None
            return candidate.lower()
        if value.startswith("0x") and len(value) == 42:
            if int(value, 16) == 0:
                return None
            return value.lower()
        return value

    def _decode_address_word(self, word: str) -> str | None:
        if len(word) != 64:
            return None
        try:
            candidate = "0x" + word[-40:]
            if int(candidate, 16) == 0:
                return None
            return candidate.lower()
        except ValueError:
            return None

    def _decode_abi_address_array(self, value: object) -> list[str] | None:
        if isinstance(value, list):
            return [str(item) for item in value if self._normalize_address(str(item))]
        if not isinstance(value, str) or not value.startswith("0x"):
            return None
        payload = value.removeprefix("0x")
        if len(payload) < 128 or len(payload) % 64 != 0:
            return None
        words = [payload[index : index + 64] for index in range(0, len(payload), 64)]
        try:
            offset = int(words[0], 16) // 32
            length = int(words[offset], 16)
        except (ValueError, IndexError):
            return None
        assets: list[str] = []
        for word in words[offset + 1 : offset + 1 + length]:
            address = self._decode_address_word(word)
            if address:
                assets.append(address)
        return assets

    def _parse_configuration(self, data: int) -> dict[str, int | bool]:
        return {
            "ltv_bps": data & 0xFFFF,
            "liquidation_threshold_bps": (data >> 16) & 0xFFFF,
            "decimals": (data >> 48) & 0xFF,
            "active": bool((data >> 56) & 1),
            "frozen": bool((data >> 57) & 1),
            "borrowing_enabled": bool((data >> 58) & 1),
            "stable_borrow_enabled": bool((data >> 59) & 1),
        }

    def _decode_abi_reserve_data(self, asset: str, value: object) -> AaveReserveMetadata | None:
        if not isinstance(value, str) or not value.startswith("0x"):
            return None
        payload = value.removeprefix("0x")
        if len(payload) < 64 * 12:
            return None
        words = [payload[index : index + 64] for index in range(0, len(payload), 64)]
        try:
            config = self._parse_configuration(int(words[0], 16))
        except ValueError:
            config = {}
        return AaveReserveMetadata(
            asset=asset,
            a_token=self._decode_address_word(words[8]) if len(words) > 8 else None,
            stable_debt_token=self._decode_address_word(words[9]) if len(words) > 9 else None,
            variable_debt_token=self._decode_address_word(words[10]) if len(words) > 10 else None,
            interest_rate_strategy=self._decode_address_word(words[11]) if len(words) > 11 else None,
            decimals=config.get("decimals"),
            ltv_bps=config.get("ltv_bps"),
            liquidation_threshold_bps=config.get("liquidation_threshold_bps"),
            borrowing_enabled=config.get("borrowing_enabled"),
            stable_borrow_enabled=config.get("stable_borrow_enabled"),
            active=config.get("active"),
            frozen=config.get("frozen"),
            discovery_status="decoded",
        )

    def _reserve_from_fixture(self, asset: str, value: object) -> AaveReserveMetadata | None:
        if isinstance(value, AaveReserveMetadata):
            return value
        if not isinstance(value, dict):
            return None
        return AaveReserveMetadata(
            asset=str(value.get("asset", asset)),
            symbol=str(value.get("symbol", "unknown")),
            a_token=value.get("a_token"),
            stable_debt_token=value.get("stable_debt_token"),
            variable_debt_token=value.get("variable_debt_token"),
            interest_rate_strategy=value.get("interest_rate_strategy"),
            decimals=value.get("decimals"),
            ltv_bps=value.get("ltv_bps"),
            liquidation_threshold_bps=value.get("liquidation_threshold_bps"),
            borrowing_enabled=value.get("borrowing_enabled"),
            stable_borrow_enabled=value.get("stable_borrow_enabled"),
            active=value.get("active"),
            frozen=value.get("frozen"),
            discovery_status=str(value.get("discovery_status", "fixture")),
            notes=list(value.get("notes", [])),
        )

    def _decode_reserve_data(self, asset: str, value: object) -> AaveReserveMetadata | None:
        return self._reserve_from_fixture(asset, value) or self._decode_abi_reserve_data(asset, value)

    def _discover_reserves(self, client: EvmReadonlyClient | None, pool_address: str | None, notes: list[str]) -> AaveV3ReadOnlyMetadata:
        if client is None or pool_address is None:
            notes.append("reserve_discovery_unavailable")
            return AaveV3ReadOnlyMetadata(reserve_discovery_status="unavailable", reserve_cap=self.max_reserves, notes=["pool_unavailable"])
        try:
            raw_assets = client.eth_call(pool_address, EvmCallBuilder.aave_pool_get_reserves_list())
            reserve_assets = self._decode_abi_address_array(raw_assets)
        except Exception:
            reserve_assets = None
        if not reserve_assets:
            notes.append("reserve_list_unresolved")
            return AaveV3ReadOnlyMetadata(reserve_discovery_status="unavailable", reserve_cap=self.max_reserves, notes=["reserve_list_unresolved"])

        reserve_notes: list[str] = []
        limited_assets = reserve_assets[: self.max_reserves]
        if len(reserve_assets) > self.max_reserves:
            reserve_notes.append(f"reserve_discovery_limited_to_{self.max_reserves}")
            notes.append(f"reserve_discovery_limited_to_{self.max_reserves}")

        reserves: list[AaveReserveMetadata] = []
        unresolved = 0
        for asset in limited_assets:
            try:
                raw_data = client.eth_call(pool_address, EvmCallBuilder.aave_pool_get_reserve_data(asset))
            except Exception:
                raw_data = None
            reserve = self._decode_reserve_data(asset, raw_data)
            if reserve is None:
                unresolved += 1
                reserve = AaveReserveMetadata(asset=asset, discovery_status="decode_unavailable", notes=["reserve_data_decode_unavailable"])
            reserves.append(reserve)

        if unresolved == 0 and len(limited_assets) == len(reserve_assets):
            status = "fully_discovered"
        elif reserves:
            status = "partially_discovered"
        else:
            status = "unavailable"
        notes.append(f"reserve_discovery_status_{status}")
        if unresolved:
            notes.append("reserve_data_decode_unavailable")
            reserve_notes.append("reserve_data_decode_unavailable")
        return AaveV3ReadOnlyMetadata(reserves=reserves, reserve_discovery_status=status, reserve_cap=self.max_reserves, notes=reserve_notes)

    def resolve(self, request: ProtocolResolutionRequest, readonly_client_or_arena: object | None = None) -> ProtocolResolutionResult:
        review = self.scope_review(request)
        root = self._root_for(request)
        if root is None:
            return ProtocolResolutionResult(
                target=None,
                scope_review=review,
                error_code=MISSING_PROTOCOL_ROOT_ADDRESS,
                discovery_status="missing_root",
            )

        notes: list[str] = ["evm_fork_twin_readonly_resolution", "executable_fork_drills_gated_until_adapter_ready"]
        contracts: list[dict[str, Any]] = [{"name": "PoolAddressesProvider", "address": root, "category": "admin_config"}]
        oracle_sources: list[str] = []
        admin_roles = ["pool_admin", "risk_admin"]

        client = readonly_client_or_arena if isinstance(readonly_client_or_arena, EvmReadonlyClient) else None
        unresolved_count = 0
        pool_address: str | None = None
        if client is None:
            notes.append("readonly_client_unavailable_partial_resolution")
            unresolved_count = len(AAVE_PROVIDER_CALLS)
        else:
            for name, call_factory in AAVE_PROVIDER_CALLS.items():
                try:
                    address = self._normalize_address(client.eth_call(root, call_factory()))
                except Exception:
                    address = None
                if address:
                    contracts.append({"name": f"AaveV3{name}", "address": str(address), "category": AAVE_CATEGORIES[name]})
                    if name == "Pool":
                        pool_address = str(address)
                    if name == "PriceOracle":
                        oracle_sources.append(f"AaveV3{name}")
                else:
                    unresolved_count += 1
                    notes.append(f"unresolved_{name}")

        reserve_metadata = self._discover_reserves(client, pool_address, notes)
        for index, reserve in enumerate(reserve_metadata.reserves, start=1):
            contracts.extend(reserve.token_contracts(index))

        if not oracle_sources and any(contract["category"] == "oracle" for contract in contracts):
            oracle_sources = [contract["name"] for contract in contracts if contract["category"] == "oracle"]

        if client is None:
            discovery_status = "unavailable"
        elif unresolved_count == 0:
            discovery_status = "fully_discovered"
        else:
            discovery_status = "partially_discovered"
        notes.append(f"discovery_status_{discovery_status}")

        critical_assets = [reserve.symbol for reserve in reserve_metadata.reserves if reserve.symbol != "unknown"]
        if not critical_assets:
            critical_assets = ["aave_v3_assets_pending_scope_review"]

        target = TargetProtocolSpec(
            protocol_name="aave_v3",
            runtime="evm",
            network_name=request.network,
            fork_block=None if request.fork_block == "latest" else request.fork_block,  # type: ignore[arg-type]
            target_mode="resolver",
            deployment_sources=["local_evm_fork_twin_readonly"],
            in_scope_contracts=contracts,
            critical_assets=critical_assets,
            oracle_sources=oracle_sources,
            governance_contracts=["AaveGovernance"],
            admin_roles=admin_roles,
            protocol_metadata={"aave_v3": reserve_metadata.safe_dict()},
            authorized_scope=False,
            scope_confirmed=False,
        )
        return ProtocolResolutionResult(target=target, scope_review=review, notes=notes, discovery_status=discovery_status)
