from __future__ import annotations

from dataclasses import dataclass

from core.capability_boundary import PermanentForbiddenCapability


PUBLIC_WORLD_SIDE_EFFECTS_FORBIDDEN = (
    "External public-world behavior is forbidden. "
    "Internal sealed-lab equivalents must be modeled with maximum realism."
)

KOREAN_SEALED_LAB_PRINCIPLE = (
    "외부 세계에서는 금지한다. 내부 실험실에서는 현실과 똑같이, 오히려 더 극한적으로 구현한다."
)

RECON_STRONGER_THAN_RED_KO = "Red가 최강이려면 Recon은 더 최강이어야 한다."
RECON_STRONGER_THAN_RED_EN = "For Red to be world-class, Recon must be stronger than Red."


@dataclass(frozen=True)
class ContainmentDecision:
    allowed: bool
    reason: str
    phase2b_execution_enabled: bool = False


def public_world_capability_decision(capability: PermanentForbiddenCapability) -> ContainmentDecision:
    return ContainmentDecision(
        allowed=False,
        reason=f"FORBIDDEN_OUTSIDE_MODELED_INSIDE:{capability.value}",
        phase2b_execution_enabled=False,
    )


def sealed_lab_modeling_decision(modeled_capability: str, *, phase2b_gate_open: bool = False) -> ContainmentDecision:
    if phase2b_gate_open:
        return ContainmentDecision(
            allowed=False,
            reason=(
                "MODEL_ONLY_IN_PHASE_2A5_R: this policy stub documents future sealed-lab capability "
                "but does not enable Phase 2B execution"
            ),
            phase2b_execution_enabled=False,
        )
    return ContainmentDecision(
        allowed=True,
        reason=f"ALLOWED_AS_MODEL_OR_REVIEW_ONLY:{modeled_capability}",
        phase2b_execution_enabled=False,
    )
