from __future__ import annotations

from recon.recon_engine import RiskHypothesis
from redteam.drills.admin_role_change_drill import ExecutableAdminRoleChangeDrill
from redteam.drills.governance_payload_drill import ExecutableGovernancePayloadDrill
from redteam.drills.liquidity_shock_drill import ExecutableLiquidityShockDrill
from redteam.drills.multi_stage_drill import ExecutableMultiStageDrill
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.drills.vault_accounting_drill import ExecutableVaultAccountingDrill

_DRILL_BY_RISK = {
    "oracle_dependency": ExecutableOracleDivergenceDrill,
    "liquidity_pressure": ExecutableLiquidityShockDrill,
    "vault_accounting": ExecutableVaultAccountingDrill,
    "multi_stage_composition": ExecutableMultiStageDrill,
    "governance_risk": ExecutableGovernancePayloadDrill,
    "admin_role_risk": ExecutableAdminRoleChangeDrill,
}


def plan_drills(hypotheses: list[RiskHypothesis]) -> list[object]:
    drills = []
    for hypothesis in hypotheses:
        drill_cls = _DRILL_BY_RISK.get(hypothesis.risk_type, ExecutableOracleDivergenceDrill)
        drills.append(drill_cls())
    return drills
