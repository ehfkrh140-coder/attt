from __future__ import annotations

from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.local_tx_intent import LocalTxIntent


class ExecutableDecoyPressureDrill(ExecutableOracleDivergenceDrill):
    drill_id = "DRILL-DECOY-PRESSURE-001"
    risk_type = "decoy_pressure"

    async def arm(self, arena, context):
        return [LocalTxIntent("mock://pool", "benign_decoy", "safe:benign-decoy", 0, "user", "local-normal", "mock-only") for _ in range(50)]
