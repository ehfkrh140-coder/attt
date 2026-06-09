from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Runtime = Literal["evm", "sui_move", "mock"]
TargetMode = Literal["manifest", "resolver", "mock"]


@dataclass(frozen=True)
class TargetProtocolSpec:
    protocol_name: str
    runtime: Runtime
    network_name: str
    fork_block: int | None
    target_mode: TargetMode
    deployment_sources: list[str] = field(default_factory=list)
    in_scope_contracts: list[dict[str, Any]] = field(default_factory=list)
    out_of_scope_contracts: list[dict[str, Any]] = field(default_factory=list)
    critical_assets: list[str] = field(default_factory=list)
    oracle_sources: list[str] = field(default_factory=list)
    dex_dependencies: list[str] = field(default_factory=list)
    governance_contracts: list[str] = field(default_factory=list)
    admin_roles: list[str] = field(default_factory=list)
    authorized_scope: bool = False
    scope_confirmed: bool = False

    @property
    def in_scope_addresses(self) -> set[str]:
        return {str(c.get("address", c.get("name", ""))).lower() for c in self.in_scope_contracts}

    def is_executable_scope(self) -> bool:
        return self.authorized_scope and self.scope_confirmed and bool(self.in_scope_contracts)


def mock_target(scope_confirmed: bool = True) -> TargetProtocolSpec:
    return TargetProtocolSpec(
        protocol_name="MockLendingVault",
        runtime="mock",
        network_name="local-mock",
        fork_block=None,
        target_mode="mock",
        deployment_sources=["targets/examples/mock_lending_vault.yaml"],
        in_scope_contracts=[
            {"name": "MockVault", "address": "mock://vault", "category": "vault"},
            {"name": "MockOracle", "address": "mock://oracle", "category": "oracle"},
            {"name": "MockDexPool", "address": "mock://pool", "category": "dex_pool"},
            {"name": "MockCircuitBreaker", "address": "mock://circuit-breaker", "category": "circuit_breaker"},
        ],
        critical_assets=["MOCK-USD", "MOCK-COLLATERAL"],
        oracle_sources=["MockOracle", "MockDexPool"],
        dex_dependencies=["MockDexPool"],
        governance_contracts=["MockGovernance"],
        admin_roles=["pauser", "guardian"],
        authorized_scope=scope_confirmed,
        scope_confirmed=scope_confirmed,
    )
