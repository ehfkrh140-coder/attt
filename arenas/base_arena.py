from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from core.safety import SafetyGuard
from redteam.local_tx_intent import LocalTxIntent


class BaseArena(ABC):
    runtime: str
    rpc_url: str
    chain_id: int
    is_local: bool

    def __init__(self, safety_guard: SafetyGuard | None = None) -> None:
        self.safety_guard = safety_guard or SafetyGuard()
        self.pending_txs: list[LocalTxIntent] = []
        self.executed_txs: list[LocalTxIntent] = []
        self.action_trace: list[dict[str, Any]] = []
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._snapshot_counter = 0

    @abstractmethod
    def get_state(self) -> dict[str, Any]: ...

    @abstractmethod
    def execute_local_tx(self, tx: LocalTxIntent) -> dict[str, Any]: ...

    def snapshot(self) -> str:
        self._snapshot_counter += 1
        snapshot_id = f"snap-{self._snapshot_counter}"
        self._snapshots[snapshot_id] = deepcopy(self.get_state())
        return snapshot_id

    def revert(self, snapshot_id: str) -> None:
        self.restore_state(deepcopy(self._snapshots[snapshot_id]))

    @abstractmethod
    def restore_state(self, state: dict[str, Any]) -> None: ...

    def submit_pending(self, tx: LocalTxIntent) -> None:
        self.pending_txs.append(tx)

    def mine_pending(self, defense_first: bool = True) -> list[dict[str, Any]]:
        ordered = sorted(self.pending_txs, key=lambda tx: (tx.sender_role != "guardian") if defense_first else False)
        receipts = [self.execute_local_tx(tx) for tx in ordered]
        self.pending_txs.clear()
        return receipts
