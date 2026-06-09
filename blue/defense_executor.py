from __future__ import annotations

from blue.action_planner import DefenseAction


def execute_defense(arena, action: DefenseAction) -> dict[str, object]:
    if action.intent is None:
        return {"action": action.action_type, "executed": False}
    arena.submit_pending(action.intent)
    return {"action": action.action_type, "executed": True}
