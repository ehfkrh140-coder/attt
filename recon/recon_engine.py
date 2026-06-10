from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.errors import ValidationError
from core.invariants import InvariantSpec
from recon.hypothesis_generator import generate_hypotheses
from recon.invariant_generator import generate_invariants
from targets.target_schema import TargetProtocolSpec

CATEGORY_KEYWORDS = {
    "vault": ("vault",),
    "oracle": ("oracle", "pricefeed", "price_feed"),
    "dex_pool": ("dex", "pool", "amm", "liquidity"),
    "circuit_breaker": ("circuit", "breaker", "pauser", "pause"),
    "governance": ("governance", "governor", "timelock"),
    "admin_config": ("admin", "config", "configurator", "owner"),
    "lending_pool": ("lending", "borrow", "loan"),
    "reserve_asset": ("reserve", "asset", "token"),
    "a_token": ("a_token", "atoken"),
    "stable_debt_token": ("stable_debt",),
    "variable_debt_token": ("variable_debt",),
    "lst": ("lst", "staking", "staked"),
    "keeper": ("keeper", "rebalance", "automation"),
}


@dataclass(frozen=True)
class RiskHypothesis:
    hypothesis_id: str
    risk_type: str
    summary: str
    affected_targets: list[str]
    invariant_ids: list[str]
    recommended_drill: str
    dependency_path: str = ""
    recommended_blue_control: str = "manual_review"


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
        categorized_contracts = [self._normalize_contract(contract, target.runtime) for contract in target.in_scope_contracts]
        attack_surface_map = self._build_attack_surface_map(target, categorized_contracts)
        contract_graph = self._build_contract_graph(target, categorized_contracts)
        dependency_graph = self._build_dependency_graph(target, categorized_contracts, contract_graph)
        critical_paths = [str(path.get("label", path)) for path in dependency_graph.get("critical_paths", [])]
        invariants = generate_invariants(attack_surface_map, dependency_graph)
        hypotheses = generate_hypotheses(invariants, dependency_graph, target.protocol_name)
        return ReconReport(
            target_protocol=target.protocol_name,
            attack_surface_map=attack_surface_map,
            contract_graph=contract_graph,
            dependency_graph=dependency_graph,
            critical_paths=critical_paths,
            invariants=invariants,
            risk_hypotheses=hypotheses,
            red_drill_recommendations=list(dict.fromkeys(h.recommended_drill for h in hypotheses)),
            blue_control_recommendations=list(dict.fromkeys(h.recommended_blue_control for h in hypotheses)),
            scope_review={
                "scope_confirmed": target.scope_confirmed,
                "authorized_scope": target.authorized_scope,
                "target_mode": target.target_mode,
                "in_scope_contract_count": len(target.in_scope_contracts),
            },
        )

    def _normalize_contract(self, contract: dict[str, Any], runtime: str) -> dict[str, Any]:
        name = str(contract.get("name") or contract.get("address") or "unknown")
        address = str(contract.get("address") or name)
        category = str(contract.get("category") or self._infer_category(name, address))
        return {
            "name": name,
            "address": address,
            "category": category,
            "runtime": runtime,
            "in_scope": True,
            "dependencies": list(contract.get("dependencies", [])),
            "metadata": dict(contract.get("metadata", {})),
        }

    def _infer_category(self, name: str, address: str) -> str:
        haystack = f"{name} {address}".lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                return category
        return "unknown"

    def _by_category(self, contracts: list[dict[str, Any]], *categories: str) -> list[dict[str, Any]]:
        return [contract for contract in contracts if contract["category"] in categories]

    def _build_attack_surface_map(self, target: TargetProtocolSpec, contracts: list[dict[str, Any]]) -> dict[str, Any]:
        vaults = self._by_category(contracts, "vault", "lending_pool", "lst")
        oracles = self._by_category(contracts, "oracle")
        liquidity = self._by_category(contracts, "dex_pool")
        governance = self._by_category(contracts, "governance")
        circuit_breakers = self._by_category(contracts, "circuit_breaker")
        reserve_assets = self._by_category(contracts, "reserve_asset")
        debt_tokens = self._by_category(contracts, "stable_debt_token", "variable_debt_token")
        return {
            "protocol_name": target.protocol_name,
            "runtime": target.runtime,
            "critical_contracts": contracts,
            "price_sensitive_contracts": vaults,
            "liquidity_dependencies": liquidity,
            "oracle_dependencies": oracles or list(target.oracle_sources),
            "governance_entrypoints": governance or [self._external_dependency(name, "governance") for name in target.governance_contracts],
            "admin_roles": list(target.admin_roles),
            "vaults": vaults,
            "reserve_assets": reserve_assets,
            "debt_tokens": debt_tokens,
            "circuit_breakers": circuit_breakers,
            "external_dependencies": {
                "oracle_sources": list(target.oracle_sources),
                "dex_dependencies": list(target.dex_dependencies),
                "governance_contracts": list(target.governance_contracts),
                "critical_assets": list(target.critical_assets),
                "protocol_metadata": dict(target.protocol_metadata),
            },
        }

    def _external_dependency(self, name: str, category: str) -> dict[str, Any]:
        return {"name": name, "address": name, "category": category, "runtime": "external", "in_scope": False}

    def _build_contract_graph(self, target: TargetProtocolSpec, contracts: list[dict[str, Any]]) -> dict[str, Any]:
        nodes = contracts
        edges: list[dict[str, str]] = []
        vaults = self._by_category(contracts, "vault", "lending_pool", "lst")
        oracles = self._by_category(contracts, "oracle")
        dex_pools = self._by_category(contracts, "dex_pool")
        reserve_assets = self._by_category(contracts, "reserve_asset")
        debt_tokens = self._by_category(contracts, "stable_debt_token", "variable_debt_token")
        circuit_breakers = self._by_category(contracts, "circuit_breaker")
        governance = self._by_category(contracts, "governance")
        admin_configs = self._by_category(contracts, "admin_config")

        for vault in vaults:
            for oracle in oracles:
                edges.append(self._edge(vault, oracle, "price_reference"))
            for pool in dex_pools:
                edges.append(self._edge(vault, pool, "liquidity_dependency"))
            for reserve in reserve_assets:
                edges.append(self._edge(vault, reserve, "reserve_accounting_dependency"))
            for breaker in circuit_breakers:
                edges.append(self._edge(breaker, vault, "pause_control"))
        for debt_token in debt_tokens:
            for reserve in reserve_assets:
                if reserve["address"] in debt_token.get("dependencies", []):
                    edges.append(self._edge(debt_token, reserve, "debt_token_underlying"))
        for gov in governance:
            for admin in admin_configs:
                edges.append(self._edge(gov, admin, "governance_admin_control"))
        for contract in contracts:
            for dependency in contract.get("dependencies", []):
                target_node = self._find_contract(contracts, str(dependency))
                if target_node:
                    edges.append(self._edge(contract, target_node, "declared_dependency"))
        return {"nodes": nodes, "edges": edges, "runtime": target.runtime}

    def _find_contract(self, contracts: list[dict[str, Any]], dependency: str) -> dict[str, Any] | None:
        lowered = dependency.lower()
        for contract in contracts:
            if lowered in {contract["name"].lower(), contract["address"].lower()}:
                return contract
        return None

    def _edge(self, source: dict[str, Any], target: dict[str, Any], edge_type: str) -> dict[str, str]:
        return {"source": source["address"], "target": target["address"], "type": edge_type}

    def _build_dependency_graph(
        self,
        target: TargetProtocolSpec,
        contracts: list[dict[str, Any]],
        contract_graph: dict[str, Any],
    ) -> dict[str, Any]:
        vaults = self._by_category(contracts, "vault", "lending_pool", "lst")
        oracles = self._by_category(contracts, "oracle")
        dex_pools = self._by_category(contracts, "dex_pool")
        reserve_assets = self._by_category(contracts, "reserve_asset")
        debt_tokens = self._by_category(contracts, "stable_debt_token", "variable_debt_token")
        governance = self._by_category(contracts, "governance")
        admin_configs = self._by_category(contracts, "admin_config")
        circuit_breakers = self._by_category(contracts, "circuit_breaker")

        oracle_paths = [
            {"from": oracle["address"], "to": vault["address"], "label": f"{oracle['name']} -> {vault['name']} price-sensitive path"}
            for oracle in oracles
            for vault in vaults
        ]
        liquidity_paths = [
            {"from": pool["address"], "to": vault["address"], "label": f"{pool['name']} liquidity -> {vault['name']} accounting/withdrawal path"}
            for pool in dex_pools
            for vault in vaults
        ]
        vault_paths = [
            {"from": vault["address"], "to": vault["address"], "label": f"{vault['name']} accounting -> share/NAV path"}
            for vault in vaults
        ]
        reserve_paths = [
            {"from": reserve["address"], "to": vault["address"], "label": f"{reserve['name']} reserve -> {vault['name']} collateral/debt path"}
            for reserve in reserve_assets
            for vault in vaults
        ]
        debt_paths = [
            {"from": debt["address"], "to": reserve["address"], "label": f"{debt['name']} -> {reserve['name']} debt accounting path"}
            for debt in debt_tokens
            for reserve in reserve_assets
            if reserve["address"] in debt.get("dependencies", [])
        ]
        governance_paths = [
            {"from": gov["address"], "to": admin["address"], "label": f"{gov['name']} -> {admin['name']} admin config path"}
            for gov in governance
            for admin in admin_configs
        ] or [
            {"from": name, "to": "admin_review", "label": f"{name} -> admin review path"}
            for name in target.governance_contracts
        ]
        admin_paths = [{"from": role, "to": "critical_control", "label": f"{role} -> privileged control path"} for role in target.admin_roles]
        circuit_breaker_paths = [
            {"from": breaker["address"], "to": vault["address"], "label": f"{breaker['name']} -> {vault['name']} pause path"}
            for breaker in circuit_breakers
            for vault in vaults
        ]
        critical_paths = oracle_paths + liquidity_paths + reserve_paths + debt_paths + governance_paths + circuit_breaker_paths
        if oracle_paths and liquidity_paths and vault_paths:
            critical_paths.append({"from": "composed_dependencies", "to": vaults[0]["address"], "label": "oracle + liquidity + vault composed risk path"})
        return {
            "oracle_sources": [contract["name"] for contract in oracles] or list(target.oracle_sources),
            "dex_dependencies": [contract["name"] for contract in dex_pools] or list(target.dex_dependencies),
            "governance_contracts": [contract["name"] for contract in governance] or list(target.governance_contracts),
            "admin_roles": list(target.admin_roles),
            "critical_assets": list(target.critical_assets),
            "oracle_paths": oracle_paths,
            "liquidity_paths": liquidity_paths,
            "vault_paths": vault_paths,
            "reserve_paths": reserve_paths,
            "debt_paths": debt_paths,
            "reserve_assets": [contract["name"] for contract in reserve_assets],
            "governance_paths": governance_paths,
            "admin_paths": admin_paths,
            "circuit_breaker_paths": circuit_breaker_paths,
            "critical_paths": critical_paths,
            "contract_edges": contract_graph["edges"],
        }
