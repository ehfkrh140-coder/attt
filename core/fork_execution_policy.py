from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ForkExecutionMode(str, Enum):
    DISABLED = "disabled"
    READ_ONLY_ONLY = "read_only_only"
    LOCAL_EXECUTION_DRY_RUN = "local_execution_dry_run"
    LOCAL_EXECUTION_ENABLED = "local_execution_enabled"


@dataclass(frozen=True)
class ForkExecutionPreconditions:
    live_readonly_smoke_passed: bool = False
    target_manifest_reviewed: bool = False
    dependency_graph_reviewed: bool = False
    snapshot_plan_present: bool = False
    rollback_plan_present: bool = False
    value_zero_enforced: bool = False
    scope_confirmed: bool = False
    adapter_ready: bool = False
    explicit_user_enable: bool = False

    def all_gates_satisfied(self) -> bool:
        return all(
            (
                self.live_readonly_smoke_passed,
                self.target_manifest_reviewed,
                self.dependency_graph_reviewed,
                self.snapshot_plan_present,
                self.rollback_plan_present,
                self.value_zero_enforced,
                self.scope_confirmed,
                self.adapter_ready,
                self.explicit_user_enable,
            )
        )


def default_fork_execution_mode() -> ForkExecutionMode:
    return ForkExecutionMode.DISABLED


def is_fork_execution_allowed(
    mode: ForkExecutionMode = ForkExecutionMode.DISABLED,
    preconditions: ForkExecutionPreconditions | None = None,
) -> bool:
    return mode == ForkExecutionMode.LOCAL_EXECUTION_ENABLED and bool(preconditions and preconditions.all_gates_satisfied())
