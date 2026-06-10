from __future__ import annotations

from arenas.base_arena import OrderingMode
from redteam.executable_drill import BlindObservableBundle
from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class OrderflowTwin(LocalOnlyTwinComponent):
    component_name = "orderflow"
    supported_modes: tuple[str, ...] = (
        "public_local_mempool",
        "private_orderflow",
        "red_first",
        "defense_first",
        "gas_priority",
        "randomized_seeded",
        "decoy_flood",
    )

    def emit(self, mode: str) -> EnvironmentEvent:
        return EnvironmentEvent("orderflow", mode, f"local orderflow mode {mode}", visible_to_blue=mode != "private_orderflow")

    def ordering_mode_for(self, mode: str) -> OrderingMode:
        mapping: dict[str, OrderingMode] = {
            "public_local_mempool": "defense_first",
            "private_orderflow": "private_orderflow",
            "red_first": "red_first",
            "defense_first": "defense_first",
            "gas_priority": "gas_priority",
            "randomized_seeded": "randomized_seeded",
            "decoy_flood": "gas_priority",
        }
        return mapping.get(mode, "defense_first")

    def visible_pending_features(self, bundle: BlindObservableBundle, mode: str):
        if mode == "private_orderflow":
            return []
        return list(bundle.pending_features)
