from __future__ import annotations

from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS
from targets.protocol_resolvers.base import ProtocolResolutionRequest, ProtocolResolutionResult, ScopeReviewReport
from targets.target_schema import TargetProtocolSpec


class EvmGenericResolver:
    protocol_name = "evm_generic"

    def scope_review(self, request: ProtocolResolutionRequest) -> ScopeReviewReport:
        candidates = [] if request.root_address is None else [{"name": "Root", "address": request.root_address}]
        return ScopeReviewReport(
            protocol_name=request.protocol,
            twin_mode="evm_fork_twin",
            candidate_contracts=candidates,
            scope_confirmed=False,
            executable_drills_allowed=False,
            status="scope_review_only",
            reason=None if candidates else MISSING_PROTOCOL_ROOT_ADDRESS,
        )

    def resolve(self, request: ProtocolResolutionRequest, readonly_client_or_arena: object | None = None) -> ProtocolResolutionResult:
        review = self.scope_review(request)
        if request.root_address is None:
            return ProtocolResolutionResult(target=None, scope_review=review, error_code=MISSING_PROTOCOL_ROOT_ADDRESS)
        target = TargetProtocolSpec(
            protocol_name=request.protocol,
            runtime="evm",
            network_name=request.network,
            fork_block=None if request.fork_block == "latest" else request.fork_block,  # type: ignore[arg-type]
            target_mode="resolver",
            deployment_sources=["evm_fork_twin_root_address"],
            in_scope_contracts=[{"name": "Root", "address": request.root_address, "category": "admin_config"}],
            authorized_scope=False,
            scope_confirmed=False,
        )
        return ProtocolResolutionResult(target=target, scope_review=review, notes=["readonly_resolution_only"])
