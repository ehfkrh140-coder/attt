from __future__ import annotations

from dataclasses import dataclass

from targets.target_schema import TargetProtocolSpec


@dataclass(frozen=True)
class ScopeReviewReport:
    protocol_name: str
    candidate_contracts: list[dict[str, str]]
    scope_confirmed: bool
    executable_drills_allowed: bool


class TargetResolver:
    def resolve_protocol_name_only(self, protocol_name: str, network_name: str) -> ScopeReviewReport:
        return ScopeReviewReport(
            protocol_name=protocol_name,
            candidate_contracts=[{"name": f"{protocol_name}Candidate", "address": "unconfirmed://candidate"}],
            scope_confirmed=False,
            executable_drills_allowed=False,
        )

    def can_execute_drills(self, target: TargetProtocolSpec) -> bool:
        return target.is_executable_scope()
