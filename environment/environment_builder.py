from __future__ import annotations

from dataclasses import dataclass

from environment.base import EnvironmentEvent
from environment.bridge_twin import BridgeTwin
from environment.keeper_twin import KeeperTwin
from environment.liquidity_twin import LiquidityTwin
from environment.network_condition_twin import NetworkConditionTwin
from environment.offchain_data_twin import OffchainDataTwin
from environment.oracle_update_twin import OracleUpdateTwin
from environment.orderflow_twin import OrderflowTwin
from environment.user_intent_twin import UserIntentTwin


@dataclass(frozen=True)
class EnvironmentTwinSpec:
    orderflow_modes: list[str]
    keeper_modes: list[str]
    oracle_modes: list[str]
    liquidity_modes: list[str]
    bridge_modes: list[str]
    offchain_modes: list[str]
    user_intent_modes: list[str]
    network_modes: list[str]


@dataclass(frozen=True)
class EnvironmentTwin:
    spec: EnvironmentTwinSpec
    events: list[EnvironmentEvent]
    local_only: bool = True

    @property
    def covered_components(self) -> set[str]:
        return {event.component for event in self.events}


class EnvironmentTwinBuilder:
    def default_research_extreme_spec(self) -> EnvironmentTwinSpec:
        return EnvironmentTwinSpec(
            orderflow_modes=["public_local_mempool", "private_orderflow", "gas_priority", "decoy_flood"],
            keeper_modes=["delayed_keeper"],
            oracle_modes=["stale_oracle", "delayed_update"],
            liquidity_modes=["liquidity_shock"],
            bridge_modes=["message_delayed"],
            offchain_modes=["api_unavailable", "stale_data"],
            user_intent_modes=["withdrawal_burst"],
            network_modes=["gas_priority_pressure", "timestamp_jump"],
        )

    def build(self, spec: EnvironmentTwinSpec | None = None) -> EnvironmentTwin:
        spec = spec or self.default_research_extreme_spec()
        events: list[EnvironmentEvent] = []
        orderflow = OrderflowTwin()
        keeper = KeeperTwin()
        oracle = OracleUpdateTwin()
        liquidity = LiquidityTwin()
        bridge = BridgeTwin()
        offchain = OffchainDataTwin()
        user_intent = UserIntentTwin()
        network = NetworkConditionTwin()
        events.extend(orderflow.emit(mode) for mode in spec.orderflow_modes)
        for mode in spec.keeper_modes:
            events.append(getattr(keeper, mode)())
        for mode in spec.oracle_modes:
            events.append(getattr(oracle, mode)())
        for mode in spec.liquidity_modes:
            events.append(getattr(liquidity, mode)())
        for mode in spec.bridge_modes:
            events.append(getattr(bridge, mode)())
        for mode in spec.offchain_modes:
            events.append(getattr(offchain, mode)())
        for mode in spec.user_intent_modes:
            events.append(getattr(user_intent, mode)())
        for mode in spec.network_modes:
            events.append(getattr(network, mode)())
        return EnvironmentTwin(spec=spec, events=events)
