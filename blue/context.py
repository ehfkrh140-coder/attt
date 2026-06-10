from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arenas.base_arena import OrderingMode


@dataclass(frozen=True)
class DefenderContext:
    recon_report: Any | None = None
    attack_surface_map: dict[str, Any] = field(default_factory=dict)
    dependency_graph: dict[str, Any] = field(default_factory=dict)
    risk_hypotheses: list[Any] = field(default_factory=list)
    invariants: list[Any] = field(default_factory=list)
    ordering_mode: OrderingMode = "defense_first"
    visibility_mode: str = "public_local_mempool"
    current_state: dict[str, object] = field(default_factory=dict)
    recent_state_window: dict[str, object] = field(default_factory=dict)
    pending_feature_count: int = 0

    @classmethod
    def from_inputs(
        cls,
        *,
        recon_report: Any | None,
        ordering_mode: OrderingMode,
        visibility_mode: str,
        current_state: dict[str, object],
        recent_state_window: dict[str, object],
        pending_feature_count: int,
    ) -> "DefenderContext":
        return cls(
            recon_report=recon_report,
            attack_surface_map=getattr(recon_report, "attack_surface_map", {}) if recon_report else {},
            dependency_graph=getattr(recon_report, "dependency_graph", {}) if recon_report else {},
            risk_hypotheses=list(getattr(recon_report, "risk_hypotheses", [])) if recon_report else [],
            invariants=list(getattr(recon_report, "invariants", [])) if recon_report else [],
            ordering_mode=ordering_mode,
            visibility_mode=visibility_mode,
            current_state=current_state,
            recent_state_window=recent_state_window,
            pending_feature_count=pending_feature_count,
        )

    @property
    def risk_types(self) -> set[str]:
        return {str(getattr(hypothesis, "risk_type", "")) for hypothesis in self.risk_hypotheses}

    @property
    def invariant_ids(self) -> set[str]:
        return {str(getattr(invariant, "invariant_id", "")) for invariant in self.invariants}
