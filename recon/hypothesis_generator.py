from __future__ import annotations

from core.invariants import InvariantSpec

RED_DRILL_BY_RISK = {
    "oracle_dependency": "ExecutableOracleDivergenceDrill",
    "liquidity_pressure": "ExecutableLiquidityShockDrill",
    "vault_accounting": "ExecutableVaultAccountingDrill",
    "multi_stage_composition": "ExecutableMultiStageDrill",
    "reserve_configuration": "ExecutableLiquidationStressDrill",
    "reserve_configuration_review": "ExecutableLiquidationStressDrill",
    "price_source_review": "ExecutableOracleDivergenceDrill",
    "unresolved_reserve_fields_watch": "ExecutableMultiStageDrill",
    "reserve_oracle_dependency": "ExecutableOracleDivergenceDrill",
    "reserve_debt_token_dependency": "ExecutableLiquidationStressDrill",
    "governance_risk": "ExecutableGovernancePayloadDrill",
    "admin_role_risk": "ExecutableAdminRoleChangeDrill",
}

BLUE_CONTROL_BY_RISK = {
    "oracle_dependency": "pause_price_sensitive_actions",
    "liquidity_pressure": "pause_withdrawals",
    "vault_accounting": "pause_vault",
    "multi_stage_composition": "correlate_oracle_liquidity_and_vault_signals",
    "reserve_configuration": "review_reserve_configuration_and_debt_tokens",
    "reserve_configuration_review": "review_reserve_configuration_and_debt_tokens",
    "price_source_review": "review_price_source_and_oracle_feed",
    "unresolved_reserve_fields_watch": "manual_review_unresolved_reserve_fields",
    "reserve_oracle_dependency": "monitor_reserve_oracle_dependency",
    "reserve_debt_token_dependency": "monitor_reserve_debt_token_dependency",
    "governance_risk": "governance_review",
    "admin_role_risk": "admin_review",
}

DEPENDENCY_PATH_BY_RISK = {
    "oracle_dependency": "oracle -> price_sensitive_target",
    "liquidity_pressure": "dex liquidity -> vault accounting or withdrawal path",
    "vault_accounting": "vault accounting -> share/NAV consistency",
    "multi_stage_composition": "oracle + liquidity + vault path -> composed invariant pressure",
    "reserve_configuration": "reserve metadata -> collateral/debt accounting path",
    "reserve_configuration_review": "reserve metadata -> configuration review",
    "price_source_review": "reserve metadata -> price source review",
    "unresolved_reserve_fields_watch": "reserve metadata -> unresolved fields watch",
    "reserve_oracle_dependency": "oracle source -> reserve price dependency",
    "reserve_debt_token_dependency": "debt token -> reserve accounting dependency",
    "governance_risk": "governance -> admin config",
    "admin_role_risk": "admin role -> privileged protocol control",
}


def affected_targets_for_invariant(invariant: InvariantSpec, dependency_graph: dict[str, object]) -> list[str]:
    risk_type = invariant.risk_type
    paths_key = {
        "oracle_dependency": "oracle_paths",
        "liquidity_pressure": "liquidity_paths",
        "vault_accounting": "vault_paths",
        "multi_stage_composition": "critical_paths",
        "reserve_configuration": "reserve_paths",
        "reserve_configuration_review": "reserve_paths",
        "price_source_review": "reserve_oracle_paths",
        "unresolved_reserve_fields_watch": "reserve_paths",
        "reserve_oracle_dependency": "reserve_oracle_paths",
        "reserve_debt_token_dependency": "debt_paths",
        "governance_risk": "governance_paths",
        "admin_role_risk": "admin_paths",
    }.get(risk_type)
    targets = {invariant.target}
    if paths_key:
        for path in dependency_graph.get(paths_key, []):
            if isinstance(path, dict):
                for value in path.values():
                    if isinstance(value, str) and (value.startswith("mock://") or "://" in value):
                        targets.add(value)
                    elif isinstance(value, list):
                        targets.update(str(item) for item in value)
    return sorted(targets)


def generate_hypotheses(invariants: list[InvariantSpec], dependency_graph: dict[str, object], protocol_name: str):
    from recon.recon_engine import RiskHypothesis

    hypotheses: list[RiskHypothesis] = []
    for index, invariant in enumerate(invariants, start=1):
        risk_type = invariant.risk_type
        hypotheses.append(
            RiskHypothesis(
                hypothesis_id=f"RH-{risk_type.upper().replace('_', '-')}-{index:03d}",
                risk_type=risk_type,
                summary=f"{protocol_name} has {risk_type.replace('_', ' ')} exposure through {DEPENDENCY_PATH_BY_RISK.get(risk_type, 'declared target dependencies')}.",
                affected_targets=affected_targets_for_invariant(invariant, dependency_graph),
                invariant_ids=[invariant.invariant_id],
                recommended_drill=RED_DRILL_BY_RISK.get(risk_type, "ExecutableMultiStageDrill"),
                dependency_path=DEPENDENCY_PATH_BY_RISK.get(risk_type, "target dependency path"),
                recommended_blue_control=BLUE_CONTROL_BY_RISK.get(risk_type, "manual_review"),
            )
        )
    for index, watch_item in enumerate(dependency_graph.get("watch_items", []), start=1):
        risk_type = str(watch_item)
        hypotheses.append(
            RiskHypothesis(
                hypothesis_id=f"RH-WATCH-{risk_type.upper().replace('_', '-')}-{index:03d}",
                risk_type=risk_type,
                summary=f"{protocol_name} has read-only watch item {risk_type.replace('_', ' ')} from discovered reserve metadata.",
                affected_targets=affected_targets_for_invariant(
                    InvariantSpec(
                        invariant_id=f"WATCH-{index:03d}",
                        target=str(protocol_name),
                        risk_type=risk_type,
                        description="read-only metadata watch item",
                        preconditions=["read-only reserve metadata exists"],
                        check_method="manual_review",
                        failure_condition="watch item is ignored",
                        severity_if_failed="medium",
                    ),
                    dependency_graph,
                ),
                invariant_ids=[f"WATCH-{index:03d}"],
                recommended_drill=RED_DRILL_BY_RISK.get(risk_type, "ExecutableMultiStageDrill"),
                dependency_path=DEPENDENCY_PATH_BY_RISK.get(risk_type, "target dependency path"),
                recommended_blue_control=BLUE_CONTROL_BY_RISK.get(risk_type, "manual_review"),
            )
        )
    return hypotheses
