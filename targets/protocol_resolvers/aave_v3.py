from __future__ import annotations

from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS, ProtocolCatalog
from targets.protocol_resolvers.base import ProtocolResolutionRequest, ProtocolResolutionResult, ScopeReviewReport
from targets.target_schema import TargetProtocolSpec


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

    def resolve(self, request: ProtocolResolutionRequest, readonly_client_or_arena: object | None = None) -> ProtocolResolutionResult:
        review = self.scope_review(request)
        root = self._root_for(request)
        if root is None:
            return ProtocolResolutionResult(target=None, scope_review=review, error_code=MISSING_PROTOCOL_ROOT_ADDRESS)
        target = TargetProtocolSpec(
            protocol_name="aave_v3",
            runtime="evm",
            network_name=request.network,
            fork_block=None if request.fork_block == "latest" else request.fork_block,  # type: ignore[arg-type]
            target_mode="resolver",
            deployment_sources=["local_evm_fork_twin"],
            in_scope_contracts=[
                {"name": "PoolAddressesProvider", "address": root, "category": "admin_config"},
                {"name": "AaveV3Pool", "address": "resolved://aave-v3-pool", "category": "lending_pool"},
                {"name": "AaveOracle", "address": "resolved://aave-v3-oracle", "category": "oracle"},
            ],
            critical_assets=["catalog_resolved_assets_pending_local_review"],
            oracle_sources=["AaveOracle"],
            governance_contracts=["AaveGovernance"],
            admin_roles=["pool_admin", "risk_admin"],
            authorized_scope=False,
            scope_confirmed=False,
        )
        return ProtocolResolutionResult(
            target=target,
            scope_review=review,
            notes=["evm_fork_twin_readonly_resolution", "executable_fork_drills_gated_until_adapter_ready"],
        )
