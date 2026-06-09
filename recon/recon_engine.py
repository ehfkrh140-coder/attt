from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.errors import ValidationError
from core.invariants import InvariantSpec
from targets.target_schema import TargetProtocolSpec


@dataclass(frozen=True)
class RiskHypothesis:
    hypothesis_id: str
    risk_type: str
    summary: str
    affected_targets: list[str]
    invariant_ids: list[str]
    recommended_drill: str


@dataclass(frozen=True)
class ReconReport:
    target_protocol: str
    attack_surface_map: dict[str, Any]
    contract_graph: dict[str, Any]
    dependency_graph: dict[str, Any]
    critical_paths: list[str]
    invariants: list[InvariantSpec]
    risk_hypotheses: list[RiskHypothesis]
    red_drill_recommendations: list[str]
    blue_control_recommendations: list[str]
    scope_review: dict[str, Any] = field(default_factory=dict)


class ReconEngine:
    def run(self, target: TargetProtocolSpec | object) -> ReconReport:
        if not isinstance(target, TargetProtocolSpec) or target.protocol_name.lower() in {"defi", "generic"}:
            raise ValidationError("RECON_REQUIRES_TARGET_PROTOCOL_SPEC")
        contracts = [c.get("name", c.get("address")) for c in target.in_scope_contracts]
        invariants = [
            InvariantSpec(
                invariant_id="INV-ORACLE-001",
                target="mock://vault",
                risk_type="oracle_dependency",
                description="Price-sensitive actions pause or fail when oracle and pool price diverge beyond threshold.",
                preconditions=["oracle source exists", "pool reference exists"],
                check_method="oracle_deviation_within_threshold",
                failure_condition="deviation exceeds threshold and protocol remains unpaused",
                severity_if_failed="high",
            ),
            InvariantSpec(
                invariant_id="INV-VAULT-001",
                target="mock://vault",
                risk_type="vault_accounting",
                description="Vault assets must remain greater than or equal to liabilities unless paused blocks impact.",
                preconditions=["vault accounting state exists"],
                check_method="vault_accounting_consistent",
                failure_condition="liabilities exceed assets and protocol remains unpaused",
                severity_if_failed="high",
            ),
        ]
        hypotheses = [
            RiskHypothesis(
                hypothesis_id="RH-ORACLE-001",
                risk_type="oracle_dependency",
                summary=f"{target.protocol_name} has price-sensitive vault paths dependent on oracle/pool agreement.",
                affected_targets=["mock://vault", "mock://oracle", "mock://pool"],
                invariant_ids=["INV-ORACLE-001"],
                recommended_drill="ExecutableOracleDivergenceDrill",
            ),
            RiskHypothesis(
                hypothesis_id="RH-VAULT-001",
                risk_type="vault_accounting",
                summary=f"{target.protocol_name} should maintain share/NAV accounting under local pressure.",
                affected_targets=["mock://vault"],
                invariant_ids=["INV-VAULT-001"],
                recommended_drill="ExecutableVaultAccountingDrill",
            ),
        ]
        return ReconReport(
            target_protocol=target.protocol_name,
            attack_surface_map={"contracts": contracts, "oracle_sources": target.oracle_sources, "admin_roles": target.admin_roles},
            contract_graph={"MockVault": ["MockOracle", "MockDexPool", "MockCircuitBreaker"]},
            dependency_graph={"oracle": target.oracle_sources, "dex": target.dex_dependencies, "governance": target.governance_contracts},
            critical_paths=["oracle -> vault withdrawal", "pool liquidity -> vault accounting"],
            invariants=invariants,
            risk_hypotheses=hypotheses,
            red_drill_recommendations=[h.recommended_drill for h in hypotheses],
            blue_control_recommendations=["pause price-sensitive actions", "rate-limit withdrawals", "ignore benign decoy labels"],
            scope_review={"scope_confirmed": target.scope_confirmed, "authorized_scope": target.authorized_scope},
        )
