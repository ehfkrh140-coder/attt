from __future__ import annotations

from dataclasses import dataclass

from environment.environment_builder import EnvironmentTwin


@dataclass(frozen=True)
class TwinFidelityScore:
    onchain_state_fidelity: float
    orderflow_coverage: float
    keeper_coverage: float
    oracle_update_coverage: float
    liquidity_coverage: float
    bridge_coverage: float
    offchain_data_coverage: float
    user_intent_coverage: float
    network_condition_coverage: float
    unsupported_components: list[str]
    overall: float


def _coverage(component: str, twin: EnvironmentTwin | None) -> float:
    if twin is None:
        return 0.0
    return 1.0 if component in twin.covered_components else 0.0


def score_twin_fidelity(protocol_twin_mode: str, environment_twin: EnvironmentTwin | None, unsupported_components: list[str] | None = None) -> TwinFidelityScore:
    unsupported = list(unsupported_components or [])
    if protocol_twin_mode == "evm_fork_twin":
        onchain = 0.9
    elif protocol_twin_mode == "mockarena":
        onchain = 0.45
    elif protocol_twin_mode == "sui_state_twin":
        onchain = 0.0
        if "sui_state_twin_adapter" not in unsupported:
            unsupported.append("sui_state_twin_adapter")
    else:
        onchain = 0.0
    values = {
        "orderflow": _coverage("orderflow", environment_twin),
        "keeper": _coverage("keeper", environment_twin),
        "oracle_update": _coverage("oracle_update", environment_twin),
        "liquidity": _coverage("liquidity", environment_twin),
        "bridge": _coverage("bridge", environment_twin),
        "offchain_data": _coverage("offchain_data", environment_twin),
        "user_intent": _coverage("user_intent", environment_twin),
        "network_condition": _coverage("network_condition", environment_twin),
    }
    penalty = min(0.5, 0.08 * len(unsupported))
    overall = max(0.0, round((onchain + sum(values.values())) / (1 + len(values)) - penalty, 4))
    if protocol_twin_mode == "sui_state_twin" and unsupported:
        overall = min(overall, 0.35)
    return TwinFidelityScore(
        onchain_state_fidelity=onchain,
        orderflow_coverage=values["orderflow"],
        keeper_coverage=values["keeper"],
        oracle_update_coverage=values["oracle_update"],
        liquidity_coverage=values["liquidity"],
        bridge_coverage=values["bridge"],
        offchain_data_coverage=values["offchain_data"],
        user_intent_coverage=values["user_intent"],
        network_condition_coverage=values["network_condition"],
        unsupported_components=unsupported,
        overall=overall,
    )
