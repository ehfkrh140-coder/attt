from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from targets.target_schema import TargetProtocolSpec


@dataclass(frozen=True)
class ProtocolResolutionRequest:
    protocol: str
    network: str = "local"
    root_address: str | None = None
    fork_block: str | int | None = None
    explicit_mock: bool = False


@dataclass(frozen=True)
class ScopeReviewReport:
    protocol_name: str
    twin_mode: str
    candidate_contracts: list[dict[str, str]]
    scope_confirmed: bool
    executable_drills_allowed: bool
    status: str
    reason: str | None = None


@dataclass(frozen=True)
class ProtocolResolutionResult:
    target: TargetProtocolSpec | None
    scope_review: ScopeReviewReport
    error_code: str | None = None
    notes: list[str] = field(default_factory=list)


class ProtocolResolver(Protocol):
    def scope_review(self, request: ProtocolResolutionRequest) -> ScopeReviewReport: ...

    def resolve(self, request: ProtocolResolutionRequest, readonly_client_or_arena: object | None = None) -> ProtocolResolutionResult: ...
