from __future__ import annotations

from recon.recon_engine import RiskHypothesis
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.drills.vault_accounting_drill import ExecutableVaultAccountingDrill


def plan_drills(hypotheses: list[RiskHypothesis]) -> list[object]:
    drills = []
    for hypothesis in hypotheses:
        if hypothesis.risk_type == "vault_accounting":
            drills.append(ExecutableVaultAccountingDrill())
        else:
            drills.append(ExecutableOracleDivergenceDrill())
    return drills
