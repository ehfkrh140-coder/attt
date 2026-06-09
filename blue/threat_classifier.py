from __future__ import annotations

from dataclasses import dataclass

from blue.context import DefenderContext


@dataclass(frozen=True)
class ThreatFinding:
    risk_type: str
    confidence: float
    rationale: str
    severity: str = "low"


def _contexts(feature: dict[str, object]) -> set[str]:
    context = feature.get("dependency_context") or []
    return {str(item) for item in context}


def _state_float(state: dict[str, object], key: str, default: float) -> float:
    try:
        return float(state.get(key, default))
    except (TypeError, ValueError):
        return default


def _oracle_deviation(state: dict[str, object]) -> float:
    oracle = _state_float(state, "oracle_price", 0.0)
    pool = _state_float(state, "pool_price", 1.0)
    return abs(oracle - pool) / max(pool, 1.0)


def _has_recon_risk(context: DefenderContext | None, risk_type: str) -> bool:
    return context is not None and risk_type in context.risk_types


def classify(
    features: list[dict[str, object]],
    state: dict[str, object],
    context: DefenderContext | None = None,
) -> ThreatFinding:
    visibility_mode = context.visibility_mode if context else "public_local_mempool"
    if not features:
        if visibility_mode == "private_orderflow":
            deviation = _oracle_deviation(state)
            threshold = _state_float(state, "max_oracle_deviation", 0.10)
            liquidity = _state_float(state, "pool_liquidity", 1_000.0)
            liquidity_floor = _state_float(state, "min_pool_liquidity", 100.0)
            assets = _state_float(state, "vault_assets", 1_000.0)
            liabilities = _state_float(state, "vault_liabilities", 0.0)
            if deviation > threshold or liquidity < liquidity_floor or liabilities > assets:
                return ThreatFinding(
                    "private_orderflow_state_risk",
                    0.72,
                    "Private orderflow hides pending features, but arena state already shows invariant drift.",
                    "medium",
                )
        return ThreatFinding("unknown", 0.1, "No local pending features available.", "low")

    all_contexts = set().union(*(_contexts(feature) for feature in features))
    state_hints = {str(feature.get("state_delta_hint")) for feature in features if feature.get("state_delta_hint")}
    target_categories = {str(feature.get("target_category")) for feature in features}
    clustered_count = sum(feature.get("timing_pattern") == "clustered_pending" for feature in features)
    has_clustered_timing = clustered_count >= 2
    has_new_research_state_change = any(
        feature.get("call_shape") in {"value_extraction_sensitive_call", "local_state_change"}
        and feature.get("sender_profile") == "new_research_account"
        for feature in features
    )
    noise_like = all(
        feature.get("call_shape") == "routine_local_activity"
        and not _contexts(feature)
        and feature.get("state_delta_hint") is None
        for feature in features
    )
    if noise_like:
        return ThreatFinding("benign_local_noise", 0.15, "Blind features look like routine local background activity.", "low")

    deviation = _oracle_deviation(state)
    threshold = _state_float(state, "max_oracle_deviation", 0.10)
    near_or_above_oracle_threshold = deviation >= threshold * 0.8
    liquidity = _state_float(state, "pool_liquidity", 1_000.0)
    liquidity_floor = _state_float(state, "min_pool_liquidity", 100.0)
    near_or_below_liquidity_floor = liquidity <= liquidity_floor * 1.25
    assets = _state_float(state, "vault_assets", 1_000.0)
    liabilities = _state_float(state, "vault_liabilities", 0.0)
    near_or_unsafe_accounting = liabilities >= assets * 0.9

    has_oracle = "oracle_path" in all_contexts or "price_reference_changed" in state_hints
    has_liquidity = "liquidity_path" in all_contexts or "liquidity_depth_changed" in state_hints
    has_vault = (
        "vault_path" in all_contexts
        or "vault_sensitive_path_touched" in state_hints
        or "accounting_boundary_touched" in state_hints
        or "price_sensitive_vault_module" in target_categories
    )

    if has_oracle and has_liquidity and has_vault and has_clustered_timing and _has_recon_risk(context, "multi_stage_composition"):
        return ThreatFinding(
            "multi_stage_composition",
            0.96,
            "Recon context and blind features correlate oracle, liquidity, and vault paths in one local window.",
            "critical",
        )
    if has_liquidity and near_or_below_liquidity_floor and _has_recon_risk(context, "liquidity_pressure"):
        return ThreatFinding(
            "liquidity_pressure",
            0.91,
            "Blind liquidity-path features align with arena state below or near liquidity floor.",
            "high",
        )
    if has_vault and near_or_unsafe_accounting and _has_recon_risk(context, "vault_accounting"):
        return ThreatFinding(
            "vault_accounting_pressure",
            0.90,
            "Blind vault/accounting features align with unsafe vault assets/liabilities state.",
            "high",
        )
    if has_oracle and has_vault and (near_or_above_oracle_threshold or has_clustered_timing) and _has_recon_risk(context, "oracle_dependency"):
        confidence = 0.89 if near_or_above_oracle_threshold else 0.84
        return ThreatFinding(
            "local_invariant_pressure",
            confidence,
            "Recon context links oracle and vault paths, and blind features show correlated pressure.",
            "high",
        )
    if has_oracle and has_vault and has_clustered_timing:
        return ThreatFinding(
            "local_invariant_pressure",
            0.82,
            "Blind features correlate price-reference movement, sensitive vault touch, and clustered timing.",
            "high",
        )
    if (has_oracle or has_liquidity or has_vault) and has_new_research_state_change:
        return ThreatFinding(
            "weak_invariant_signal",
            0.55,
            "One invariant-sensitive blind signal appeared, but context/state correlation is insufficient for pause.",
            "medium",
        )
    return ThreatFinding("unknown", 0.25, "Blind features do not form a strong invariant-risk correlation.", "low")
