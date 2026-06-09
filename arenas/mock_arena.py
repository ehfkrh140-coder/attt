from __future__ import annotations

from copy import deepcopy
from typing import Any

from arenas.base_arena import BaseArena
from redteam.local_tx_intent import LocalTxIntent


class MockArena(BaseArena):
    runtime = "mock"
    rpc_url = "mock://localhost"
    chain_id = 31337
    is_local = True
    adapter_ready = True

    def __init__(self) -> None:
        super().__init__()
        self.state: dict[str, Any] = {
            "oracle_price": 100.0,
            "pool_price": 100.0,
            "max_oracle_deviation": 0.10,
            "vault_assets": 1_000.0,
            "vault_liabilities": 500.0,
            "pool_liquidity": 1_000.0,
            "min_pool_liquidity": 100.0,
            "paused": False,
            "decoy_count": 0,
            "blocked_sensitive_actions": 0,
        }

    def get_state(self) -> dict[str, Any]:
        return deepcopy(self.state)

    def restore_state(self, state: dict[str, Any]) -> None:
        self.state = deepcopy(state)

    def execute_local_tx(self, tx: LocalTxIntent) -> dict[str, Any]:
        self.assert_executable_tx(tx)
        before = self.get_state()
        if tx.function_category == "defense_pause":
            self.state["paused"] = True
            self.action_trace.append({"action": "pause", "reason": tx.calldata_label})
        elif tx.function_category == "oracle_divergence":
            self.state["oracle_price"] = 150.0
            self.state["pool_price"] = 100.0
        elif tx.function_category == "price_sensitive_withdrawal":
            if self.state["paused"]:
                self.state["blocked_sensitive_actions"] += 1
            else:
                self.state["vault_assets"] -= 700.0
                self.state["vault_liabilities"] = max(self.state["vault_liabilities"], 500.0)
        elif tx.function_category == "liquidity_shock":
            self.state["pool_liquidity"] = 25.0
        elif tx.function_category == "vault_accounting_pressure":
            if not self.state["paused"]:
                self.state["vault_liabilities"] += 650.0
        elif tx.function_category == "benign_decoy":
            self.state["decoy_count"] += 1
        self.executed_txs.append(tx)
        return {"tx": tx.public_report_dict(), "before": before, "after": self.get_state()}
