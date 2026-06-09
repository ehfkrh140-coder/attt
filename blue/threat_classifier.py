from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatFinding:
    risk_type: str
    confidence: float
    rationale: str


def classify(features: list[dict[str, object]], state: dict[str, object]) -> ThreatFinding:
    categories = {str(feature.get("function_category")) for feature in features}
    decoys = sum(1 for feature in features if feature.get("function_category") == "benign_decoy")
    risky = {"oracle_divergence", "price_sensitive_withdrawal", "vault_accounting_pressure", "liquidity_shock"}
    if categories & risky:
        return ThreatFinding("local_invariant_pressure", 0.92, "Risky local function categories correlated with protected state.")
    if decoys and decoys == len(features):
        return ThreatFinding("benign_decoy_pressure", 0.15, "High volume local benign labels without invariant pressure.")
    return ThreatFinding("unknown", 0.2, "No correlated invariant pressure detected.")
