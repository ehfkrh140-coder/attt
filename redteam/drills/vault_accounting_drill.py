from __future__ import annotations

from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.local_tx_intent import LocalTxIntent


class ExecutableVaultAccountingDrill(ExecutableOracleDivergenceDrill):
    drill_id = "DRILL-VAULT-ACCOUNTING-001"
    risk_type = "vault_accounting"

    async def arm(self, arena, context):
        return [LocalTxIntent("mock://vault", "vault_accounting_pressure", "safe:vault-accounting-pressure", 0, "adversarial-researcher", "local-normal", "mock-only")]
