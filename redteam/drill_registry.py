from __future__ import annotations

from core.errors import ValidationError
from redteam.executable_drill import ExecutableDrill, StaticRedScenario

ERROR_REQUIRES_EXECUTABLE_DRILL = "RED_CHALLENGE_REQUIRES_EXECUTABLE_DRILL"

DRILL_CLASS_REGISTRY = {
    "ExecutableOracleDivergenceDrill": "redteam.drills.oracle_divergence_drill.ExecutableOracleDivergenceDrill",
    "ExecutableLiquidityShockDrill": "redteam.drills.liquidity_shock_drill.ExecutableLiquidityShockDrill",
    "ExecutableVaultAccountingDrill": "redteam.drills.vault_accounting_drill.ExecutableVaultAccountingDrill",
    "ExecutableMultiStageDrill": "redteam.drills.multi_stage_drill.ExecutableMultiStageDrill",
    "ExecutableGovernancePayloadDrill": "redteam.drills.governance_payload_drill.ExecutableGovernancePayloadDrill",
    "ExecutableAdminRoleChangeDrill": "redteam.drills.admin_role_change_drill.ExecutableAdminRoleChangeDrill",
}


def resolve_drill_class(drill_name: str) -> type:
    import importlib

    dotted = DRILL_CLASS_REGISTRY[drill_name]
    module_name, class_name = dotted.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def validate_red_challenge(challenge: object) -> ExecutableDrill:
    if isinstance(challenge, StaticRedScenario):
        raise ValidationError(ERROR_REQUIRES_EXECUTABLE_DRILL)
    required = ["precheck", "prepare", "arm", "trigger", "collect_blue_observables", "assert_impact"]
    if not all(callable(getattr(challenge, name, None)) for name in required):
        raise ValidationError(ERROR_REQUIRES_EXECUTABLE_DRILL)
    return challenge  # type: ignore[return-value]
