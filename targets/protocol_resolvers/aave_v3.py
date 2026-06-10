from __future__ import annotations

from typing import Any

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_readonly_client import EvmReadonlyClient
from targets.aave_v3_readonly import (
    AAVE_MAX_RESERVES_DEFAULT,
    AAVE_MAX_RESERVES_HARD_CAP,
    AaveReserveMetadata,
    AaveV3CoreContracts,
    AaveV3ReadOnlyDiscoveryReport,
)
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
    def __init__(self, catalog: ProtocolCatalog | None = None, *, max_reserves: int = AAVE_MAX_RESERVES_DEFAULT) -> None:
        self.catalog = catalog or ProtocolCatalog()
        self.max_reserves_requested = max_reserves
        self.max_reserves = max(0, min(max_reserves, AAVE_MAX_RESERVES_HARD_CAP))
        self.hard_cap_applied = max_reserves > AAVE_MAX_RESERVES_HARD_CAP

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

    def _hex_to_int(self, value: object) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value, 16) if value.startswith("0x") else int(value)
            except ValueError:
                return None
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

    def _configuration_from_value(self, value: object) -> dict[str, int | bool] | None:
        if isinstance(value, dict):
            return {key: val for key, val in value.items() if key in {"ltv_bps", "liquidation_threshold_bps", "decimals", "active", "frozen", "borrowing_enabled", "stable_borrow_enabled"}}
        parsed = self._hex_to_int(value)
        return self._parse_configuration(parsed) if parsed is not None else None

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
            asset_price=value.get("asset_price"),
            oracle_source=value.get("oracle_source"),
            discovery_status=str(value.get("discovery_status", "fixture")),
            unresolved_fields=list(value.get("unresolved_fields", [])),
            watch_items=list(value.get("watch_items", [])),
            notes=list(value.get("notes", [])),
        )

    def _decode_reserve_data(self, asset: str, value: object) -> AaveReserveMetadata | None:
        return self._reserve_from_fixture(asset, value) or self._decode_abi_reserve_data(asset, value)

    def _call_optional(self, client: EvmReadonlyClient, to: str | None, call_label: str, call_factory) -> tuple[object | None, str | None]:
        if not to:
            return None, call_label
        try:
            value = client.eth_call(to, call_factory())
        except Exception:
            value = None
        return (value, None) if value not in {None, "", "0x"} else (None, call_label)

    def _read_acl_roles(self, client: EvmReadonlyClient | None, acl_manager: str | None, unresolved_calls: list[str]) -> tuple[str | None, str | None]:
        if client is None or acl_manager is None:
            unresolved_calls.extend(["aave_acl_get_pool_admin_role", "aave_acl_get_risk_admin_role"])
            return None, None
        pool_role, pool_error = self._call_optional(client, acl_manager, "aave_acl_get_pool_admin_role", EvmCallBuilder.aave_acl_get_pool_admin_role)
        risk_role, risk_error = self._call_optional(client, acl_manager, "aave_acl_get_risk_admin_role", EvmCallBuilder.aave_acl_get_risk_admin_role)
        if pool_error:
            unresolved_calls.append(pool_error)
        if risk_error:
            unresolved_calls.append(risk_error)
        return (str(pool_role) if pool_role else None, str(risk_role) if risk_role else None)

    def _merge_config(self, reserve: AaveReserveMetadata, config: dict[str, int | bool] | None) -> AaveReserveMetadata:
        if not config:
            return reserve
        return AaveReserveMetadata(
            asset=reserve.asset,
            symbol=reserve.symbol,
            a_token=reserve.a_token,
            stable_debt_token=reserve.stable_debt_token,
            variable_debt_token=reserve.variable_debt_token,
            interest_rate_strategy=reserve.interest_rate_strategy,
            decimals=int(config.get("decimals", reserve.decimals)) if config.get("decimals", reserve.decimals) is not None else None,
            ltv_bps=int(config.get("ltv_bps", reserve.ltv_bps)) if config.get("ltv_bps", reserve.ltv_bps) is not None else None,
            liquidation_threshold_bps=int(config.get("liquidation_threshold_bps", reserve.liquidation_threshold_bps)) if config.get("liquidation_threshold_bps", reserve.liquidation_threshold_bps) is not None else None,
            borrowing_enabled=bool(config.get("borrowing_enabled", reserve.borrowing_enabled)) if config.get("borrowing_enabled", reserve.borrowing_enabled) is not None else None,
            stable_borrow_enabled=bool(config.get("stable_borrow_enabled", reserve.stable_borrow_enabled)) if config.get("stable_borrow_enabled", reserve.stable_borrow_enabled) is not None else None,
            active=bool(config.get("active", reserve.active)) if config.get("active", reserve.active) is not None else None,
            frozen=bool(config.get("frozen", reserve.frozen)) if config.get("frozen", reserve.frozen) is not None else None,
            asset_price=reserve.asset_price,
            oracle_source=reserve.oracle_source,
            discovery_status=reserve.discovery_status,
            unresolved_fields=list(reserve.unresolved_fields),
            watch_items=list(reserve.watch_items),
            notes=list(reserve.notes),
        )

    def _enrich_reserve(
        self,
        client: EvmReadonlyClient,
        reserve: AaveReserveMetadata,
        pool_address: str,
        oracle_address: str | None,
    ) -> AaveReserveMetadata:
        unresolved_fields = list(reserve.unresolved_fields)
        watch_items = set(reserve.watch_items)

        try:
            configuration_value = client.eth_call(pool_address, EvmCallBuilder.aave_pool_get_configuration(reserve.asset))
        except Exception:
            configuration_value = None
        configuration = self._configuration_from_value(configuration_value)
        if configuration is None:
            unresolved_fields.append("configuration")
            watch_items.add("reserve_configuration_review")
            watch_items.add("unresolved_reserve_fields_watch")
        else:
            reserve = self._merge_config(reserve, configuration)
            watch_items.add("reserve_configuration_review")

        price_value = None
        source = None
        if oracle_address:
            try:
                price_value = client.eth_call(oracle_address, EvmCallBuilder.aave_oracle_get_asset_price(reserve.asset))
            except Exception:
                price_value = None
            try:
                source = self._normalize_address(client.eth_call(oracle_address, EvmCallBuilder.aave_oracle_get_source_of_asset(reserve.asset)))
            except Exception:
                source = None
        price = self._hex_to_int(price_value)
        if price is None:
            unresolved_fields.append("asset_price")
            watch_items.add("price_source_review")
            watch_items.add("unresolved_reserve_fields_watch")
        else:
            watch_items.add("price_source_review")
        if source is None:
            unresolved_fields.append("oracle_source")
            watch_items.add("price_source_review")
            watch_items.add("unresolved_reserve_fields_watch")
        else:
            watch_items.add("reserve_oracle_dependency")
        if reserve.variable_debt_token or reserve.stable_debt_token:
            watch_items.add("reserve_debt_token_dependency")

        return AaveReserveMetadata(
            asset=reserve.asset,
            symbol=reserve.symbol,
            a_token=reserve.a_token,
            stable_debt_token=reserve.stable_debt_token,
            variable_debt_token=reserve.variable_debt_token,
            interest_rate_strategy=reserve.interest_rate_strategy,
            decimals=reserve.decimals,
            ltv_bps=reserve.ltv_bps,
            liquidation_threshold_bps=reserve.liquidation_threshold_bps,
            borrowing_enabled=reserve.borrowing_enabled,
            stable_borrow_enabled=reserve.stable_borrow_enabled,
            active=reserve.active,
            frozen=reserve.frozen,
            asset_price=price,
            oracle_source=source,
            discovery_status=reserve.discovery_status,
            unresolved_fields=sorted(set(unresolved_fields)),
            watch_items=sorted(watch_items),
            notes=list(reserve.notes),
        )

    def _discover_reserves(
        self,
        client: EvmReadonlyClient | None,
        core_contracts: AaveV3CoreContracts,
        unresolved_calls: list[str],
    ) -> AaveV3ReadOnlyDiscoveryReport:
        if client is None or core_contracts.pool is None:
            unresolved_calls.append("aave_pool_get_reserves_list")
            return AaveV3ReadOnlyDiscoveryReport(
                core_contracts=core_contracts,
                reserve_discovery_status="unavailable",
                max_reserves_requested=self.max_reserves_requested,
                max_reserves_processed=self.max_reserves,
                hard_cap_applied=self.hard_cap_applied,
                truncated=self.hard_cap_applied,
                unresolved_calls=sorted(set(unresolved_calls)),
                watch_items=["unresolved_reserve_fields_watch"],
                warnings=["pool_unavailable"],
            )
        try:
            raw_assets = client.eth_call(core_contracts.pool, EvmCallBuilder.aave_pool_get_reserves_list())
            reserve_assets = self._decode_abi_address_array(raw_assets)
        except Exception:
            reserve_assets = None
        if not reserve_assets:
            unresolved_calls.append("aave_pool_get_reserves_list")
            return AaveV3ReadOnlyDiscoveryReport(
                core_contracts=core_contracts,
                reserve_discovery_status="unavailable",
                max_reserves_requested=self.max_reserves_requested,
                max_reserves_processed=self.max_reserves,
                hard_cap_applied=self.hard_cap_applied,
                truncated=self.hard_cap_applied,
                unresolved_calls=sorted(set(unresolved_calls)),
                watch_items=["unresolved_reserve_fields_watch"],
                warnings=["reserve_list_unresolved"],
            )

        limited_assets = reserve_assets[: self.max_reserves]
        truncated = len(reserve_assets) > len(limited_assets) or self.hard_cap_applied
        warnings: list[str] = []
        if truncated:
            warnings.append("reserve_list_truncated")
            warnings.append(f"reserve_discovery_limited_to_{self.max_reserves}")

        reserves: list[AaveReserveMetadata] = []
        unresolved_reserve_fields: list[str] = []
        watch_items = {"reserve_configuration_review"}
        unresolved = 0
        for asset in limited_assets:
            try:
                raw_data = client.eth_call(core_contracts.pool, EvmCallBuilder.aave_pool_get_reserve_data(asset))
            except Exception:
                raw_data = None
            reserve = self._decode_reserve_data(asset, raw_data)
            if reserve is None:
                unresolved += 1
                reserve = AaveReserveMetadata(
                    asset=asset,
                    discovery_status="decode_unavailable",
                    unresolved_fields=["reserve_data"],
                    watch_items=["unresolved_reserve_fields_watch"],
                    notes=["reserve_data_decode_unavailable"],
                )
            reserve = self._enrich_reserve(client, reserve, core_contracts.pool, core_contracts.price_oracle)
            unresolved_reserve_fields.extend(f"{reserve.symbol}:{field}" for field in reserve.unresolved_fields)
            watch_items.update(reserve.watch_items)
            reserves.append(reserve)

        if unresolved == 0 and not truncated:
            status = "fully_discovered"
        elif reserves:
            status = "partially_discovered"
        else:
            status = "unavailable"
        if unresolved:
            warnings.append("reserve_data_decode_unavailable")
        return AaveV3ReadOnlyDiscoveryReport(
            core_contracts=core_contracts,
            reserves=reserves,
            reserve_discovery_status=status,
            max_reserves_requested=self.max_reserves_requested,
            max_reserves_processed=self.max_reserves,
            hard_cap_applied=self.hard_cap_applied,
            truncated=truncated,
            unresolved_calls=sorted(set(unresolved_calls)),
            unresolved_reserve_fields=sorted(set(unresolved_reserve_fields)),
            watch_items=sorted(watch_items),
            warnings=sorted(set(warnings)),
        )

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
        unresolved_calls: list[str] = []

        client = readonly_client_or_arena if isinstance(readonly_client_or_arena, EvmReadonlyClient) else None
        unresolved_count = 0
        discovered_core: dict[str, str | None] = {"Pool": None, "PoolConfigurator": None, "PriceOracle": None, "ACLManager": None}
        if client is None:
            notes.append("readonly_client_unavailable_partial_resolution")
            unresolved_count = len(AAVE_PROVIDER_CALLS)
            unresolved_calls.extend(f"aave_provider_{name.lower()}" for name in AAVE_PROVIDER_CALLS)
        else:
            for name, call_factory in AAVE_PROVIDER_CALLS.items():
                try:
                    address = self._normalize_address(client.eth_call(root, call_factory()))
                except Exception:
                    address = None
                if address:
                    discovered_core[name] = str(address)
                    contracts.append({"name": f"AaveV3{name}", "address": str(address), "category": AAVE_CATEGORIES[name]})
                    if name == "PriceOracle":
                        oracle_sources.append(f"AaveV3{name}")
                else:
                    unresolved_count += 1
                    note = f"unresolved_{name}"
                    notes.append(note)
                    unresolved_calls.append(call_factory().safe_label)

        pool_admin_role, risk_admin_role = self._read_acl_roles(client, discovered_core["ACLManager"], unresolved_calls)
        core_contracts = AaveV3CoreContracts(
            pool_addresses_provider=root,
            pool=discovered_core["Pool"],
            pool_configurator=discovered_core["PoolConfigurator"],
            price_oracle=discovered_core["PriceOracle"],
            acl_manager=discovered_core["ACLManager"],
            pool_admin_role=pool_admin_role,
            risk_admin_role=risk_admin_role,
        )
        reserve_report = self._discover_reserves(client, core_contracts, unresolved_calls)
        for index, reserve in enumerate(reserve_report.reserves, start=1):
            contracts.extend(reserve.token_contracts(index))
        for note in reserve_report.warnings:
            notes.append(note)
        for field in reserve_report.unresolved_reserve_fields:
            notes.append(f"unresolved_reserve_field_{field}")
        notes.append(f"reserve_discovery_status_{reserve_report.reserve_discovery_status}")
        if reserve_report.truncated:
            notes.append("reserve_discovery_truncated")

        if not oracle_sources and any(contract["category"] == "oracle" for contract in contracts):
            oracle_sources = [contract["name"] for contract in contracts if contract["category"] == "oracle"]

        if client is None:
            discovery_status = "unavailable"
        elif unresolved_count == 0:
            discovery_status = "fully_discovered"
        else:
            discovery_status = "partially_discovered"
        notes.append(f"discovery_status_{discovery_status}")

        critical_assets = [reserve.symbol for reserve in reserve_report.reserves if reserve.symbol != "unknown"]
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
            protocol_metadata={"aave_v3": reserve_report.safe_dict()},
            authorized_scope=False,
            scope_confirmed=False,
        )
        return ProtocolResolutionResult(target=target, scope_review=review, notes=notes, discovery_status=discovery_status)
