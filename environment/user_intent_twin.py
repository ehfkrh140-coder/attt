from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class UserIntentTwin(LocalOnlyTwinComponent):
    component_name = "user_intent"

    def withdrawal_burst(self) -> EnvironmentEvent:
        return EnvironmentEvent("user_intent", "withdrawal_burst", "local users submit clustered withdrawals")

    def deposit_burst(self) -> EnvironmentEvent:
        return EnvironmentEvent("user_intent", "deposit_burst", "local users submit clustered deposits")

    def panic_exit(self) -> EnvironmentEvent:
        return EnvironmentEvent("user_intent", "panic_exit", "local panic exit intent burst")
