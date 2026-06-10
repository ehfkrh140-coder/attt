from dataclasses import dataclass

from arenas.base_arena import BaseArena


@dataclass
class SnapshotManager:
    arena: BaseArena

    def snapshot(self) -> str:
        return self.arena.snapshot()

    def revert(self, snapshot_id: str) -> None:
        self.arena.revert(snapshot_id)
