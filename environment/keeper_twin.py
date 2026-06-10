from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class KeeperTwin(LocalOnlyTwinComponent):
    component_name = "keeper"

    def delayed_keeper(self) -> EnvironmentEvent:
        return EnvironmentEvent("keeper", "delayed_keeper", "local keeper action delayed beyond expected window")

    def missing_keeper(self) -> EnvironmentEvent:
        return EnvironmentEvent("keeper", "missing_keeper", "local keeper action omitted for stress testing")

    def burst_keeper(self) -> EnvironmentEvent:
        return EnvironmentEvent("keeper", "burst_keeper", "local keeper actions clustered in one window")
