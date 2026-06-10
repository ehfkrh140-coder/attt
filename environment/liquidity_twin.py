from __future__ import annotations

from environment.base import EnvironmentEvent, LocalOnlyTwinComponent


class LiquidityTwin(LocalOnlyTwinComponent):
    component_name = "liquidity"

    def liquidity_shock(self) -> EnvironmentEvent:
        return EnvironmentEvent("liquidity", "liquidity_shock", "local pool depth drops below research threshold")

    def slippage_spike(self) -> EnvironmentEvent:
        return EnvironmentEvent("liquidity", "slippage_spike", "local slippage pressure increases")
