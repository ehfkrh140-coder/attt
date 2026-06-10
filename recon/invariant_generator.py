from __future__ import annotations

from core.invariants import InvariantSpec


def generate_invariants(attack_surface_map: dict[str, object], dependency_graph: dict[str, object]) -> list[InvariantSpec]:
    invariants: list[InvariantSpec] = []
    vault_targets = [str(contract["address"]) for contract in attack_surface_map.get("vaults", [])]
    liquidity_targets = [str(contract["address"]) for contract in attack_surface_map.get("liquidity_dependencies", [])]
    governance_targets = [str(contract["address"]) for contract in attack_surface_map.get("governance_entrypoints", [])]
    admin_roles = [str(role) for role in attack_surface_map.get("admin_roles", [])]
    oracle_paths = dependency_graph.get("oracle_paths", [])
    liquidity_paths = dependency_graph.get("liquidity_paths", [])
    reserve_paths = dependency_graph.get("reserve_paths", [])

    primary_vault = vault_targets[0] if vault_targets else str(attack_surface_map.get("protocol_name", "target"))
    primary_liquidity = liquidity_targets[0] if liquidity_targets else primary_vault

    if oracle_paths and vault_targets:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-ORACLE-001",
                target=primary_vault,
                risk_type="oracle_dependency",
                description="Price-sensitive actions should pause or fail when price-reference dependencies diverge beyond threshold.",
                preconditions=["oracle dependency exists", "price-sensitive target exists"],
                check_method="oracle_deviation_within_threshold",
                failure_condition="oracle/pool deviation exceeds threshold while target remains unpaused",
                severity_if_failed="high",
            )
        )
    if liquidity_paths:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-LIQUIDITY-001",
                target=primary_liquidity,
                risk_type="liquidity_pressure",
                description="Liquidity-dependent paths should block or degrade when local liquidity depth falls below floor.",
                preconditions=["liquidity dependency exists"],
                check_method="liquidity_above_floor",
                failure_condition="pool liquidity below configured floor while target remains unpaused",
                severity_if_failed="high",
            )
        )
    if reserve_paths and vault_targets:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-RESERVE-001",
                target=primary_vault,
                risk_type="reserve_configuration",
                description="Reserve collateral and debt-token configuration should remain consistent with local risk limits.",
                preconditions=["reserve metadata exists", "lending pool target exists"],
                check_method="reserve_configuration_reviewed",
                failure_condition="reserve configuration changes or missing debt metadata are not surfaced for defense review",
                severity_if_failed="medium",
            )
        )
    if vault_targets:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-VAULT-001",
                target=primary_vault,
                risk_type="vault_accounting",
                description="Vault assets and liabilities should remain accounting-consistent under local pressure.",
                preconditions=["vault/accounting target exists"],
                check_method="vault_accounting_consistent",
                failure_condition="liabilities exceed assets while target remains unpaused",
                severity_if_failed="high",
            )
        )
    if oracle_paths and liquidity_paths and vault_targets:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-MULTI-STAGE-001",
                target=primary_vault,
                risk_type="multi_stage_composition",
                description="Combined price-reference, liquidity, and vault-path pressure should be detected as a composed local risk.",
                preconditions=["oracle dependency exists", "liquidity dependency exists", "vault target exists"],
                check_method="multi_invariant_composition",
                failure_condition="one or more composed local invariants fail in a correlated window",
                severity_if_failed="critical",
            )
        )
    if governance_targets:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-GOVERNANCE-001",
                target=governance_targets[0],
                risk_type="governance_risk",
                description="Governance execution paths should require review before high-risk local actions.",
                preconditions=["governance entrypoint exists"],
                check_method="governance_review_required",
                failure_condition="high-risk governance path executes without review opportunity",
                severity_if_failed="medium",
            )
        )
    if admin_roles:
        invariants.append(
            InvariantSpec(
                invariant_id="INV-ADMIN-001",
                target=primary_vault,
                risk_type="admin_role_risk",
                description="Critical admin role changes should be detected and routed for review.",
                preconditions=["admin role declared"],
                check_method="admin_change_detected",
                failure_condition="critical admin change is not detected",
                severity_if_failed="medium",
            )
        )
    return invariants
