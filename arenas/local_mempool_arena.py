from __future__ import annotations

from arenas.mock_arena import MockArena
from redteam.local_tx_intent import LocalTxIntent


class LocalMempoolArena(MockArena):
    def __init__(self, private_orderflow: bool = False) -> None:
        super().__init__()
        self.automine = False
        self.private_orderflow = private_orderflow

    def visible_pending_features(self) -> list[dict[str, object]]:
        if self.private_orderflow:
            return []
        return [
            {
                "target": tx.target,
                "function_category": tx.function_category,
                "calldata_label": tx.calldata_label,
                "value": tx.value,
                "sender_role": tx.sender_role,
                "gas_strategy": tx.gas_strategy,
                "safety_scope": tx.safety_scope,
            }
            for tx in self.pending_txs
        ]

    def submit_local_intents(self, intents: list[LocalTxIntent]) -> None:
        for intent in intents:
            self.submit_pending(intent)
