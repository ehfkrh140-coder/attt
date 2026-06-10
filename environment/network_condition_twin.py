from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class NetworkConditionTwin(LocalOnlyTwinComponent):
    component_name = "network_condition"

    def local_block_delay(self) -> EnvironmentEvent:
        return EnvironmentEvent("network_condition", "local_block_delay", "local block production delayed")

    def timestamp_jump(self) -> EnvironmentEvent:
        return EnvironmentEvent("network_condition", "timestamp_jump", "local timestamp jump applied through arena controls")

    def gas_priority_pressure(self) -> EnvironmentEvent:
        return EnvironmentEvent("network_condition", "gas_priority_pressure", "local gas priority pressure simulated")
