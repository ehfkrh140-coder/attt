from __future__ import annotations

import pytest

from core.errors import ValidationError
from recon.recon_engine import ReconEngine
from redteam.drill_registry import resolve_drill_class, validate_red_challenge
from targets.target_schema import TargetProtocolSpec


def rich_target() -> TargetProtocolSpec:
    return TargetProtocolSpec(
        protocol_name="ResearchVaultX",
        runtime="mock",
        network_name="local-mock",
        fork_block=None,
        target_mode="manifest",
        deployment_sources=["unit-test-manifest"],
        in_scope_contracts=[
            {"name": "AlphaVault", "address": "local://alpha-vault", "category": "vault"},
            {"name": "AlphaPriceFeed", "address": "local://alpha-oracle", "category": "oracle"},
            {"name": "AlphaLiquidityPool", "address": "local://alpha-pool", "category": "dex_pool"},
            {"name": "AlphaBreaker", "address": "local://alpha-breaker", "category": "circuit_breaker"},
            {"name": "AlphaGovernor", "address": "local://alpha-governor", "category": "governance"},
            {"name": "AlphaConfigurator", "address": "local://alpha-config", "category": "admin_config"},
        ],
        critical_assets=["aUSD", "aETH"],
        oracle_sources=["AlphaPriceFeed"],
        dex_dependencies=["AlphaLiquidityPool"],
        governance_contracts=["AlphaGovernor"],
        admin_roles=["guardian", "risk_admin"],
        authorized_scope=True,
        scope_confirmed=True,
    )


def target_without_oracle_or_dex() -> TargetProtocolSpec:
    return TargetProtocolSpec(
        protocol_name="VaultOnly",
        runtime="mock",
        network_name="local-mock",
        fork_block=None,
        target_mode="manifest",
        in_scope_contracts=[{"name": "SoloVault", "address": "local://solo-vault", "category": "vault"}],
        authorized_scope=True,
        scope_confirmed=True,
    )


def inferred_name_target() -> TargetProtocolSpec:
    return TargetProtocolSpec(
        protocol_name="DifferentNamesProtocol",
        runtime="mock",
        network_name="local-mock",
        fork_block=None,
        target_mode="manifest",
        in_scope_contracts=[
            {"name": "BetaAssetVault", "address": "local://beta-asset-accounting"},
            {"name": "BetaOracleModule", "address": "local://beta-price"},
            {"name": "BetaDexPool", "address": "local://beta-liquidity"},
        ],
        critical_assets=["bUSD"],
        oracle_sources=["BetaOracleModule"],
        dex_dependencies=["BetaDexPool"],
        authorized_scope=True,
        scope_confirmed=True,
    )


def test_recon_builds_attack_surface_from_target_spec():
    report = ReconEngine().run(rich_target())
    surface = report.attack_surface_map
    assert surface["protocol_name"] == "ResearchVaultX"
    assert surface["runtime"] == "mock"
    assert {contract["address"] for contract in surface["vaults"]} == {"local://alpha-vault"}
    assert {contract["address"] for contract in surface["oracle_dependencies"]} == {"local://alpha-oracle"}
    assert {contract["address"] for contract in surface["liquidity_dependencies"]} == {"local://alpha-pool"}
    assert {contract["address"] for contract in surface["governance_entrypoints"]} == {"local://alpha-governor"}
    assert surface["admin_roles"] == ["guardian", "risk_admin"]


def test_recon_builds_contract_graph_from_target_spec():
    graph = ReconEngine().run(rich_target()).contract_graph
    nodes = {node["address"]: node for node in graph["nodes"]}
    edges = {(edge["source"], edge["target"], edge["type"]) for edge in graph["edges"]}
    assert nodes["local://alpha-vault"]["category"] == "vault"
    assert nodes["local://alpha-oracle"]["category"] == "oracle"
    assert ("local://alpha-vault", "local://alpha-oracle", "price_reference") in edges
    assert ("local://alpha-vault", "local://alpha-pool", "liquidity_dependency") in edges
    assert ("local://alpha-breaker", "local://alpha-vault", "pause_control") in edges
    assert ("local://alpha-governor", "local://alpha-config", "governance_admin_control") in edges


def test_recon_builds_dependency_graph_from_target_spec():
    dependency_graph = ReconEngine().run(rich_target()).dependency_graph
    assert dependency_graph["oracle_paths"]
    assert dependency_graph["liquidity_paths"]
    assert dependency_graph["governance_paths"]
    assert dependency_graph["admin_paths"]
    assert any("oracle" in path["label"].lower() or "price" in path["label"].lower() for path in dependency_graph["oracle_paths"])
    assert any("liquidity" in path["label"].lower() for path in dependency_graph["liquidity_paths"])


def test_recon_generates_invariants_by_contract_category():
    rich_invariants = {invariant.invariant_id for invariant in ReconEngine().run(rich_target()).invariants}
    assert {"INV-ORACLE-001", "INV-LIQUIDITY-001", "INV-VAULT-001", "INV-MULTI-STAGE-001", "INV-GOVERNANCE-001", "INV-ADMIN-001"} <= rich_invariants

    vault_only_invariants = {invariant.invariant_id for invariant in ReconEngine().run(target_without_oracle_or_dex()).invariants}
    assert "INV-VAULT-001" in vault_only_invariants
    assert "INV-ORACLE-001" not in vault_only_invariants
    assert "INV-LIQUIDITY-001" not in vault_only_invariants


def test_recon_generates_drill_recommendations_by_risk_type():
    report = ReconEngine().run(rich_target())
    risk_to_drill = {hypothesis.risk_type: hypothesis.recommended_drill for hypothesis in report.risk_hypotheses}
    assert risk_to_drill["oracle_dependency"] == "ExecutableOracleDivergenceDrill"
    assert risk_to_drill["liquidity_pressure"] == "ExecutableLiquidityShockDrill"
    assert risk_to_drill["vault_accounting"] == "ExecutableVaultAccountingDrill"
    assert risk_to_drill["multi_stage_composition"] == "ExecutableMultiStageDrill"
    assert risk_to_drill["governance_risk"] == "ExecutableGovernancePayloadDrill"
    assert risk_to_drill["admin_role_risk"] == "ExecutableAdminRoleChangeDrill"
    assert "pause_price_sensitive_actions" in report.blue_control_recommendations
    assert "pause_withdrawals" in report.blue_control_recommendations
    assert "pause_vault" in report.blue_control_recommendations


def test_recon_no_hardcoded_mock_vault_only():
    report = ReconEngine().run(inferred_name_target())
    assert "mock://vault" not in str(report)
    assert any(node["address"] == "local://beta-asset-accounting" for node in report.contract_graph["nodes"])
    assert any(hypothesis.affected_targets for hypothesis in report.risk_hypotheses)
    assert {"INV-ORACLE-001", "INV-LIQUIDITY-001", "INV-VAULT-001"} <= {invariant.invariant_id for invariant in report.invariants}


def test_recon_requires_target_protocol_spec():
    with pytest.raises(ValidationError, match="RECON_REQUIRES_TARGET_PROTOCOL_SPEC"):
        ReconEngine().run("DeFi")


def test_recon_recommendations_feed_existing_red_drills():
    report = ReconEngine().run(rich_target())
    for drill_name in report.red_drill_recommendations:
        drill_cls = resolve_drill_class(drill_name)
        validate_red_challenge(drill_cls())
