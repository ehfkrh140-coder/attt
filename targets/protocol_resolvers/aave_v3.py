from __future__ import annotations

from typing import Any

from adapters.evm_call_builder import EvmCallBuilder
from adapters.evm_readonly_client import EvmReadonlyClient
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
    def __init__(self, catalog: ProtocolCatalog | None = None) -> None:
        self.catalog = catalog or ProtocolCatalog()

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

    def resolve(self, request: ProtocolResolutionRequest, readonly_client_or_arena: object | None = None) -> ProtocolResolutionResult:
        review = self.scope_review(request)
        root = self._root_for(request)
        if root is None:
            return ProtocolResolutionResult(target=None, scope_review=review, error_code=MISSING_PROTOCOL_ROOT_ADDRESS)

        notes: list[str] = ["evm_fork_twin_readonly_resolution", "executable_fork_drills_gated_until_adapter_ready"]
        contracts: list[dict[str, Any]] = [{"name": "PoolAddressesProvider", "address": root, "category": "admin_config"}]
        oracle_sources: list[str] = []
        admin_roles = ["pool_admin", "risk_admin"]

        client = readonly_client_or_arena if isinstance(readonly_client_or_arena, EvmReadonlyClient) else None
        if client is None:
            notes.append("readonly_client_unavailable_partial_resolution")
        else:
            for name, call_factory in AAVE_PROVIDER_CALLS.items():
                try:
                    address = self._normalize_address(client.eth_call(root, call_factory()))
                except Exception:
                    address = None
                if address:
                    contracts.append({"name": f"AaveV3{name}", "address": str(address), "category": AAVE_CATEGORIES[name]})
                    if name == "PriceOracle":
                        oracle_sources.append(f"AaveV3{name}")
                else:
                    notes.append(f"unresolved_{name}")

        if not oracle_sources and any(contract["category"] == "oracle" for contract in contracts):
            oracle_sources = [contract["name"] for contract in contracts if contract["category"] == "oracle"]

        target = TargetProtocolSpec(
            protocol_name="aave_v3",
            runtime="evm",
            network_name=request.network,
            fork_block=None if request.fork_block == "latest" else request.fork_block,  # type: ignore[arg-type]
            target_mode="resolver",
            deployment_sources=["local_evm_fork_twin_readonly"],
            in_scope_contracts=contracts,
            critical_assets=["aave_v3_assets_pending_scope_review"],
            oracle_sources=oracle_sources,
            governance_contracts=["AaveGovernance"],
            admin_roles=admin_roles,
            authorized_scope=False,
            scope_confirmed=False,
        )
        return ProtocolResolutionResult(target=target, scope_review=review, notes=notes)
