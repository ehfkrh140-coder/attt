from __future__ import annotations

from dataclasses import dataclass

from blue.threat_classifier import ThreatFinding
from redteam.local_tx_intent import LocalTxIntent


@dataclass(frozen=True)
class DefenseAction:
    action_type: str
    intent: LocalTxIntent | None
    rationale: str


def plan_action(finding: ThreatFinding) -> DefenseAction:
    if finding.confidence >= 0.8:
        return DefenseAction(
            action_type="pause_price_sensitive_actions",
            intent=LocalTxIntent("mock://circuit-breaker", "defense_pause", "safe:defense-pause", 0, "guardian", "local-defense-first", "mock-only"),
            rationale=finding.rationale,
        )
    return DefenseAction("monitor", None, finding.rationale)
