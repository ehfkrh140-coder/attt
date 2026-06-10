from __future__ import annotations

from dataclasses import dataclass

from blue.threat_classifier import ThreatFinding
from redteam.local_tx_intent import LocalTxIntent


@dataclass(frozen=True)
class DefenseAction:
    action_type: str
    intent: LocalTxIntent | None
    rationale: str


def _pause_intent(label: str) -> LocalTxIntent:
    return LocalTxIntent("mock://circuit-breaker", "defense_pause", label, 0, "guardian", "local-defense-first", "mock-only")


def plan_action(finding: ThreatFinding) -> DefenseAction:
    if finding.risk_type == "local_invariant_pressure":
        return DefenseAction(
            "pause_price_sensitive_actions",
            _pause_intent("safe:defense-pause"),
            finding.rationale,
        )
    if finding.risk_type == "liquidity_pressure":
        return DefenseAction(
            "pause_withdrawals",
            _pause_intent("safe:liquidity-defense-pause"),
            finding.rationale,
        )
    if finding.risk_type == "vault_accounting_pressure":
        return DefenseAction(
            "pause_vault",
            _pause_intent("safe:vault-defense-pause"),
            finding.rationale,
        )
    if finding.risk_type == "multi_stage_composition":
        return DefenseAction(
            "pause_price_sensitive_actions",
            _pause_intent("safe:multi-stage-defense-pause"),
            finding.rationale,
        )
    if finding.risk_type == "governance_risk":
        return DefenseAction("governance_review", None, finding.rationale)
    if finding.risk_type == "admin_role_risk":
        return DefenseAction("admin_review", None, finding.rationale)
    if finding.risk_type == "private_orderflow_state_risk":
        return DefenseAction("alert_only", None, finding.rationale)
    if finding.confidence >= 0.9 and finding.severity in {"high", "critical"}:
        return DefenseAction("pause_price_sensitive_actions", _pause_intent("safe:defense-pause"), finding.rationale)
    return DefenseAction("monitor", None, finding.rationale)
