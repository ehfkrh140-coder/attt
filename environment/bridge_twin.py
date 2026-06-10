from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class BridgeTwin(LocalOnlyTwinComponent):
    component_name = "bridge"

    def message_delayed(self) -> EnvironmentEvent:
        return EnvironmentEvent("bridge", "message_delayed", "local bridge message delayed stub")

    def remote_chain_unavailable(self) -> EnvironmentEvent:
        return EnvironmentEvent("bridge", "remote_chain_unavailable", "remote chain represented as local unavailable state")

    def external_calls_enabled(self) -> bool:
        return False
