from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatFinding:
    risk_type: str
    confidence: float
    rationale: str


def _contexts(feature: dict[str, object]) -> set[str]:
    context = feature.get("dependency_context") or []
    return {str(item) for item in context}


def classify(features: list[dict[str, object]], state: dict[str, object]) -> ThreatFinding:
    if not features:
        return ThreatFinding("unknown", 0.1, "No local pending features available.")

    has_price_reference_change = any(
        feature.get("state_delta_hint") == "price_reference_changed" and "oracle_path" in _contexts(feature)
        for feature in features
    )
    has_sensitive_vault_touch = any(
        feature.get("target_category") == "price_sensitive_vault_module" or "vault_path" in _contexts(feature)
        for feature in features
    )
    has_clustered_timing = sum(feature.get("timing_pattern") == "clustered_pending" for feature in features) >= 2
    has_sensitive_call_shape = any(
        feature.get("call_shape") in {"value_extraction_sensitive_call", "local_state_change"}
        and feature.get("sender_profile") == "new_research_account"
        for feature in features
    )
    has_invariant_context = any(_contexts(feature) & {"oracle_path", "vault_path", "liquidity_path"} for feature in features)

    if has_price_reference_change and has_sensitive_vault_touch and has_clustered_timing:
        return ThreatFinding(
            "local_invariant_pressure",
            0.92,
            "Blind features correlate price-reference movement, sensitive vault touch, and clustered timing.",
        )
    if has_invariant_context and has_sensitive_call_shape and has_clustered_timing:
        return ThreatFinding(
            "local_invariant_pressure",
            0.82,
            "Blind features show clustered invariant-sensitive local state pressure.",
        )

    noise_like = all(
        feature.get("call_shape") == "routine_local_activity"
        and not _contexts(feature)
        and feature.get("state_delta_hint") is None
        for feature in features
    )
    if noise_like:
        return ThreatFinding("benign_local_noise", 0.15, "Blind features look like routine local background activity.")

    return ThreatFinding("unknown", 0.25, "Blind features do not form a strong invariant-risk correlation.")
