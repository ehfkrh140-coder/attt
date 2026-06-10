from __future__ import annotations

from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD
from blue.action_planner import DefenseAction


def execute_defense(arena, action: DefenseAction) -> dict[str, object]:
    if action.intent is None:
        return {"action": action.action_type, "executed": False}
    assert_executable_tx = getattr(arena, "assert_executable_tx", None)
    submit_pending = getattr(arena, "submit_pending", None)
    if not callable(assert_executable_tx) or not callable(submit_pending):
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
    assert_executable_tx(action.intent)
    submit_pending(action.intent)
    return {"action": action.action_type, "executed": True}
