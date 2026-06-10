from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.fork_execution_policy import ForkExecutionMode, ForkExecutionPreconditions, is_fork_execution_allowed
from redteam.local_tx_intent import LocalTxIntent

UNSUPPORTED_EXECUTABLE_FORK_DRILLS = "UNSUPPORTED_EXECUTABLE_FORK_DRILLS"


@dataclass
class EvmForkExecutionArena:
    """Design-only gated interface for future mediated local fork execution."""

    mode: ForkExecutionMode = ForkExecutionMode.DISABLED
    preconditions: ForkExecutionPreconditions = field(default_factory=ForkExecutionPreconditions)

    def snapshot(self) -> str:
        return "fork-execution-design-snapshot"

    def revert(self, snapshot_id: str) -> None:
        if not snapshot_id:
            raise ValueError("snapshot_id_required")

    def dry_run_intent(self, intent: LocalTxIntent) -> dict[str, Any]:
        return {
            "supported": False,
            "mode": self.mode.value,
            "value_zero": intent.value == 0,
            "execution_enabled": is_fork_execution_allowed(self.mode, self.preconditions),
            "reason": UNSUPPORTED_EXECUTABLE_FORK_DRILLS,
        }

    def execute_local_intent(self, intent: LocalTxIntent) -> dict[str, Any]:
        raise RuntimeError(UNSUPPORTED_EXECUTABLE_FORK_DRILLS)
