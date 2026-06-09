from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImpactAssertion:
    invariant_id: str
    impact_success: bool
    blocked_by_blue: bool
    state_diff: dict[str, tuple[object, object]]
    notes: list[str] = field(default_factory=list)
