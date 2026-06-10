from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class OffchainDataTwin(LocalOnlyTwinComponent):
    component_name = "offchain_data"

    def api_unavailable(self) -> EnvironmentEvent:
        return EnvironmentEvent("offchain_data", "api_unavailable", "local offchain data source unavailable stub")

    def stale_data(self) -> EnvironmentEvent:
        return EnvironmentEvent("offchain_data", "stale_data", "local offchain data is stale")

    def external_calls_enabled(self) -> bool:
        return False
