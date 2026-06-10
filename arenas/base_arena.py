from __future__ import annotations

import random
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Literal

from core.safety import SafetyGuard
from targets.target_schema import TargetProtocolSpec
from redteam.local_tx_intent import LocalTxIntent

OrderingMode = Literal["defense_first", "red_first", "gas_priority", "private_orderflow", "randomized_seeded"]
SUPPORTED_ORDERING_MODES: tuple[OrderingMode, ...] = (
    "defense_first",
    "red_first",
    "gas_priority",
    "private_orderflow",
    "randomized_seeded",
)
DEFAULT_RANDOMIZED_SEED = 1337


class BaseArena(ABC):
    runtime: str
    rpc_url: str
    chain_id: int
    is_local: bool
    adapter_ready: bool

    def __init__(self, safety_guard: SafetyGuard | None = None) -> None:
        self.safety_guard = safety_guard or SafetyGuard()
        self.pending_txs: list[LocalTxIntent] = []
        self.executed_txs: list[LocalTxIntent] = []
        self.action_trace: list[dict[str, Any]] = []
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._snapshot_counter = 0
        self.bound_target: TargetProtocolSpec | None = None

    @abstractmethod
    def get_state(self) -> dict[str, Any]: ...

    def bind_target(self, target: TargetProtocolSpec) -> None:
        self.safety_guard.assert_scope_confirmed(target)
        self.bound_target = target

    def assert_executable_tx(self, tx: LocalTxIntent) -> None:
        self.safety_guard.assert_tx_allowed(tx, self, self.bound_target)

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
        self.assert_executable_tx(tx)
        self.pending_txs.append(tx)

    def ordered_pending(self, ordering_mode: OrderingMode = "defense_first", seed: int | None = None) -> list[LocalTxIntent]:
        indexed = list(enumerate(self.pending_txs))
        if ordering_mode == "defense_first":
            return [tx for _, tx in sorted(indexed, key=lambda item: (item[1].sender_role != "guardian", item[0]))]
        if ordering_mode == "red_first":
            return [tx for _, tx in sorted(indexed, key=lambda item: (item[1].sender_role != "adversarial-researcher", item[0]))]
        if ordering_mode == "gas_priority":
            priority = {"local-defense-first": 0, "local-priority": 1, "local-normal": 2}
            return [tx for _, tx in sorted(indexed, key=lambda item: (priority.get(item[1].gas_strategy, 99), item[0]))]
        if ordering_mode == "private_orderflow":
            return self.ordered_pending("red_first", seed)
        if ordering_mode == "randomized_seeded":
            shuffled = list(self.pending_txs)
            random.Random(DEFAULT_RANDOMIZED_SEED if seed is None else seed).shuffle(shuffled)
            return shuffled
        raise ValueError(f"Unsupported ordering mode: {ordering_mode}")

    def mine_pending(
        self,
        ordering_mode: OrderingMode = "defense_first",
        seed: int | None = None,
        defense_first: bool | None = None,
    ) -> list[dict[str, Any]]:
        if defense_first is not None:
            ordering_mode = "defense_first" if defense_first else "red_first"
        ordered = self.ordered_pending(ordering_mode=ordering_mode, seed=seed)
        receipts = [self.execute_local_tx(tx) for tx in ordered]
        self.pending_txs.clear()
        return receipts
