from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class OracleUpdateTwin(LocalOnlyTwinComponent):
    component_name = "oracle_update"

    def stale_oracle(self) -> EnvironmentEvent:
        return EnvironmentEvent("oracle_update", "stale_oracle", "local oracle update window is stale")

    def delayed_update(self) -> EnvironmentEvent:
        return EnvironmentEvent("oracle_update", "delayed_update", "local oracle update is delayed")

    def sudden_update(self) -> EnvironmentEvent:
        return EnvironmentEvent("oracle_update", "sudden_update", "local oracle reference changes abruptly")
