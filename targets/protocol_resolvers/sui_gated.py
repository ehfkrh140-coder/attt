from __future__ import annotations

from targets.protocol_catalog import UNSUPPORTED_PROTOCOL_TWIN
from targets.protocol_resolvers.base import ProtocolResolutionRequest, ProtocolResolutionResult, ScopeReviewReport


class SuiGatedResolver:
    def scope_review(self, request: ProtocolResolutionRequest) -> ScopeReviewReport:
        return ScopeReviewReport(
            protocol_name=request.protocol,
            twin_mode="sui_state_twin",
            candidate_contracts=[],
            scope_confirmed=False,
            executable_drills_allowed=False,
            status="gated_unsupported_until_sui_adapter",
            reason=UNSUPPORTED_PROTOCOL_TWIN,
        )

    def resolve(self, request: ProtocolResolutionRequest, readonly_client_or_arena: object | None = None) -> ProtocolResolutionResult:
        return ProtocolResolutionResult(
            target=None,
            scope_review=self.scope_review(request),
            error_code=UNSUPPORTED_PROTOCOL_TWIN,
            notes=["sui_state_twin_adapter_not_implemented"],
        )
