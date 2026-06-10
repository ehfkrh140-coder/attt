from __future__ import annotations


def watch(arena) -> list[dict[str, object]]:
    return arena.visible_pending_features()
