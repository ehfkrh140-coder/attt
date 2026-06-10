from __future__ import annotations

from core.invariants import InvariantSpec

RED_DRILL_BY_RISK = {
    "oracle_dependency": "ExecutableOracleDivergenceDrill",
    "liquidity_pressure": "ExecutableLiquidityShockDrill",
    "vault_accounting": "ExecutableVaultAccountingDrill",
    "multi_stage_composition": "ExecutableMultiStageDrill",
    "reserve_configuration": "ExecutableLiquidationStressDrill",
    "governance_risk": "ExecutableGovernancePayloadDrill",
    "admin_role_risk": "ExecutableAdminRoleChangeDrill",
}

BLUE_CONTROL_BY_RISK = {
    "oracle_dependency": "pause_price_sensitive_actions",
    "liquidity_pressure": "pause_withdrawals",
    "vault_accounting": "pause_vault",
    "multi_stage_composition": "correlate_oracle_liquidity_and_vault_signals",
    "reserve_configuration": "review_reserve_configuration_and_debt_tokens",
    "governance_risk": "governance_review",
    "admin_role_risk": "admin_review",
}

DEPENDENCY_PATH_BY_RISK = {
    "oracle_dependency": "oracle -> price_sensitive_target",
    "liquidity_pressure": "dex liquidity -> vault accounting or withdrawal path",
    "vault_accounting": "vault accounting -> share/NAV consistency",
    "multi_stage_composition": "oracle + liquidity + vault path -> composed invariant pressure",
    "reserve_configuration": "reserve metadata -> collateral/debt accounting path",
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
    return hypotheses
