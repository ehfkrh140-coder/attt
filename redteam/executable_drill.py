from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from redteam.impact_assertion import ImpactAssertion
from redteam.local_tx_intent import LocalTxIntent


@dataclass(frozen=True)
class DrillPrecheck:
    allowed: bool
    reason: str = "OK"


@dataclass
class DrillContext:
    snapshot_id: str
    risk_hypothesis_id: str
    hidden_ground_truth: dict[str, Any] = field(default_factory=dict)


@dataclass
class DrillTrace:
    drill_id: str
    tx_intents: list[LocalTxIntent]
    state_events: list[dict[str, Any]]
    hidden_ground_truth: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlindObservableBundle:
    drill_id: str
    pending_features: list[dict[str, Any]]
    state_window: dict[str, Any]

    def assert_no_ground_truth(self) -> None:
        forbidden = {"expected_action", "hidden_ground_truth", "malicious", "answer_key"}
        haystack = str(self.__dict__).lower()
        leaked = [key for key in forbidden if key in haystack]
        if leaked:
            raise AssertionError(f"Blue observable leaked ground truth: {leaked}")


class ExecutableDrill(Protocol):
    drill_id: str
    risk_type: str
    target_protocol: str
    required_runtime: str

    async def precheck(self, arena: Any, target: Any) -> DrillPrecheck: ...
    async def prepare(self, arena: Any, target: Any) -> DrillContext: ...
    async def arm(self, arena: Any, context: DrillContext) -> list[LocalTxIntent]: ...
    async def trigger(self, arena: Any, context: DrillContext) -> DrillTrace: ...
    async def collect_blue_observables(self, trace: DrillTrace) -> BlindObservableBundle: ...
    async def assert_impact(self, arena: Any, trace: DrillTrace) -> ImpactAssertion: ...
    async def cleanup(self, arena: Any, context: DrillContext) -> None: ...


@dataclass(frozen=True)
class StaticRedScenario:
    title: str
    narrative: str
