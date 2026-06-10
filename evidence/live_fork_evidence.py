from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from core.safety import SafetyGuard


def _safe_list(values: list[str]) -> list[str]:
    return [str(value) for value in values]


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def root_label(value: str | None) -> str:
    if not value:
        return "missing-root"
    if value.startswith("aave-root") or value.startswith("fixture"):
        return str(value)
    return "root-address-provided"


def localhost_label(value: str | None) -> str:
    if not value:
        return "not-provided"
    if "127.0.0.1" in value:
        return "http://127.0.0.1:local"
    if "localhost" in value:
        return "http://localhost:local"
    if value.startswith("mock://"):
        return "fixture-local-rpc"
    return "non-local-rpc-blocked"


@dataclass(frozen=True)
class LocalForkCheckEvidence:
    reachable: bool
    chain_id: str
    client_version_status: str
    read_only_mode: bool
    transactions_enabled: bool
    safety_status: str
    notes: list[str] = field(default_factory=list)

    def safe_dict(self) -> dict[str, Any]:
        return {
            "reachable": self.reachable,
            "chain_id": self.chain_id,
            "client_version_status": self.client_version_status,
            "read_only_mode": self.read_only_mode,
            "transactions_enabled": self.transactions_enabled,
            "safety_status": self.safety_status,
            "notes": _safe_list(self.notes),
        }

    def summary_lines(self) -> list[str]:
        return [
            f"- Local fork reachable: {_yes_no(self.reachable)}",
            f"- Chain id: {self.chain_id}",
            f"- Client version status: {self.client_version_status}",
            f"- Read-only mode: {_yes_no(self.read_only_mode)}",
            f"- Transactions enabled: {_yes_no(self.transactions_enabled)}",
            f"- Safety status: {self.safety_status}",
            "- Local fork notes: " + (", ".join(self.notes) if self.notes else "none"),
        ]


@dataclass(frozen=True)
class AaveReadOnlyDiscoveryEvidence:
    protocol: str
    protocol_twin_mode: str
    root_address_label: str
    discovery_status: str
    core_contracts_count: int
    reserve_count: int
    max_reserves_requested: int
    max_reserves_processed: int
    truncated: bool
    unresolved_calls: list[str] = field(default_factory=list)
    unresolved_reserve_fields: list[str] = field(default_factory=list)
    watch_items: list[str] = field(default_factory=list)
    selected_drill_recommendations: list[str] = field(default_factory=list)
    recon_hypotheses_count: int = 0
    execution_gated: bool = True
    mockarena_fallback: bool = False

    def safe_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "protocol_twin_mode": self.protocol_twin_mode,
            "root_address_label": self.root_address_label,
            "discovery_status": self.discovery_status,
            "core_contracts_count": self.core_contracts_count,
            "reserve_count": self.reserve_count,
            "max_reserves_requested": self.max_reserves_requested,
            "max_reserves_processed": self.max_reserves_processed,
            "truncated": self.truncated,
            "unresolved_calls": _safe_list(self.unresolved_calls),
            "unresolved_reserve_fields": _safe_list(self.unresolved_reserve_fields),
            "watch_items": _safe_list(self.watch_items),
            "selected_drill_recommendations": _safe_list(self.selected_drill_recommendations),
            "recon_hypotheses_count": self.recon_hypotheses_count,
            "execution_gated": self.execution_gated,
            "mockarena_fallback": self.mockarena_fallback,
        }

    def summary_lines(self) -> list[str]:
        gated_drills = [f"{item} (gated)" for item in self.selected_drill_recommendations]
        return [
            f"- Protocol: {self.protocol}",
            f"- Protocol Twin mode: {self.protocol_twin_mode}",
            f"- Root address label: {self.root_address_label}",
            f"- Read-only discovery: {self.discovery_status}",
            f"- Core contracts count: {self.core_contracts_count}",
            f"- Reserve count: {self.reserve_count}",
            f"- Max reserves requested: {self.max_reserves_requested}",
            f"- Max reserves processed: {self.max_reserves_processed}",
            f"- Truncated: {_yes_no(self.truncated)}",
            "- Unresolved calls: " + (", ".join(self.unresolved_calls) if self.unresolved_calls else "none"),
            "- Unresolved reserve fields: "
            + (", ".join(self.unresolved_reserve_fields) if self.unresolved_reserve_fields else "none"),
            "- Watch items: " + (", ".join(self.watch_items) if self.watch_items else "none"),
            "- Selected drill recommendations gated: " + (", ".join(gated_drills) if gated_drills else "none"),
            f"- Recon hypotheses count: {self.recon_hypotheses_count}",
            f"- Execution gated: {_yes_no(self.execution_gated)}",
            f"- MockArena fallback: {_yes_no(self.mockarena_fallback)}",
        ]


@dataclass(frozen=True)
class TargetManifestReviewEvidence:
    manifest_path: str
    exists: bool
    scope_confirmed: bool
    authorized_scope: bool
    executable_drills_allowed: bool
    read_only_only: bool
    contract_count: int
    reserve_count: int
    has_protocol_metadata: bool
    safety_notes: list[str] = field(default_factory=list)

    def safe_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": self.manifest_path,
            "exists": self.exists,
            "scope_confirmed": self.scope_confirmed,
            "authorized_scope": self.authorized_scope,
            "executable_drills_allowed": self.executable_drills_allowed,
            "read_only_only": self.read_only_only,
            "contract_count": self.contract_count,
            "reserve_count": self.reserve_count,
            "has_protocol_metadata": self.has_protocol_metadata,
            "safety_notes": _safe_list(self.safety_notes),
        }

    def summary_lines(self) -> list[str]:
        return [
            f"- Target manifest: {'present' if self.exists else 'missing'}",
            f"- Manifest path label: {self.manifest_path}",
            f"- Scope confirmed: {_yes_no(self.scope_confirmed)}",
            f"- Authorized scope: {_yes_no(self.authorized_scope)}",
            f"- Executable drills allowed: {_yes_no(self.executable_drills_allowed)}",
            f"- Read-only only: {_yes_no(self.read_only_only)}",
            f"- Manifest contract count: {self.contract_count}",
            f"- Manifest reserve count: {self.reserve_count}",
            f"- Manifest has protocol metadata: {_yes_no(self.has_protocol_metadata)}",
            "- Manifest safety notes: " + (", ".join(self.safety_notes) if self.safety_notes else "none"),
        ]


@dataclass(frozen=True)
class DependencyGraphReviewEvidence:
    review_path: str
    exists: bool
    reserve_paths_count: int
    debt_paths_count: int
    reserve_oracle_paths_count: int
    watch_items_count: int
    unresolved_items_count: int
    review_status: str

    def safe_dict(self) -> dict[str, Any]:
        return {
            "review_path": self.review_path,
            "exists": self.exists,
            "reserve_paths_count": self.reserve_paths_count,
            "debt_paths_count": self.debt_paths_count,
            "reserve_oracle_paths_count": self.reserve_oracle_paths_count,
            "watch_items_count": self.watch_items_count,
            "unresolved_items_count": self.unresolved_items_count,
            "review_status": self.review_status,
        }

    def summary_lines(self) -> list[str]:
        return [
            f"- Dependency graph review: {'present' if self.exists else 'missing'}",
            f"- Dependency review path label: {self.review_path}",
            f"- Reserve paths count: {self.reserve_paths_count}",
            f"- Debt paths count: {self.debt_paths_count}",
            f"- Reserve oracle paths count: {self.reserve_oracle_paths_count}",
            f"- Dependency review watch items count: {self.watch_items_count}",
            f"- Dependency review unresolved items count: {self.unresolved_items_count}",
            f"- Dependency review status: {self.review_status}",
        ]


@dataclass(frozen=True)
class LiveForkEvidencePack:
    created_at: str
    protocol: str
    network: str
    fork_block: str
    local_rpc_url_label: str
    local_fork: LocalForkCheckEvidence
    aave_discovery: AaveReadOnlyDiscoveryEvidence
    target_manifest: TargetManifestReviewEvidence
    dependency_graph_review: DependencyGraphReviewEvidence
    phase2b_candidate_status: str = "blocked_by_default"
    missing_prerequisites: list[str] = field(default_factory=list)
    evidence_source: str = "unknown"

    @classmethod
    def now(
        cls,
        *,
        protocol: str,
        network: str,
        fork_block: str | None,
        local_rpc_url_label: str,
        local_fork: LocalForkCheckEvidence,
        aave_discovery: AaveReadOnlyDiscoveryEvidence,
        target_manifest: TargetManifestReviewEvidence,
        dependency_graph_review: DependencyGraphReviewEvidence,
        phase2b_candidate_status: str,
        missing_prerequisites: list[str],
        evidence_source: str,
    ) -> "LiveForkEvidencePack":
        return cls(
            created_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
            protocol=protocol,
            network=network,
            fork_block=str(fork_block or "not-recorded"),
            local_rpc_url_label=local_rpc_url_label,
            local_fork=local_fork,
            aave_discovery=aave_discovery,
            target_manifest=target_manifest,
            dependency_graph_review=dependency_graph_review,
            phase2b_candidate_status=phase2b_candidate_status,
            missing_prerequisites=missing_prerequisites,
            evidence_source=evidence_source,
        )

    def safe_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "protocol": self.protocol,
            "network": self.network,
            "fork_block": self.fork_block,
            "local_rpc_url_label": self.local_rpc_url_label,
            "evidence_source": self.evidence_source,
            "local_fork": self.local_fork.safe_dict(),
            "aave_discovery": self.aave_discovery.safe_dict(),
            "target_manifest": self.target_manifest.safe_dict(),
            "dependency_graph_review": self.dependency_graph_review.safe_dict(),
            "phase2b_candidate_status": self.phase2b_candidate_status,
            "missing_prerequisites": _safe_list(self.missing_prerequisites),
        }

    def safe_summary(self) -> str:
        lines = [
            "Live Fork Evidence Pack",
            f"- Created at: {self.created_at}",
            f"- Evidence source: {self.evidence_source}",
            f"- Protocol: {self.protocol}",
            f"- Network: {self.network}",
            f"- Fork block: {self.fork_block}",
            f"- Local RPC URL label: {self.local_rpc_url_label}",
            f"- Phase 2B candidate status: {self.phase2b_candidate_status}",
            "- Missing prerequisites: "
            + (", ".join(self.missing_prerequisites) if self.missing_prerequisites else "none"),
            "",
            "## Local fork check",
            *self.local_fork.summary_lines(),
            "",
            "## Aave read-only discovery",
            *self.aave_discovery.summary_lines(),
            "",
            "## Target manifest review",
            *self.target_manifest.summary_lines(),
            "",
            "## Dependency graph review",
            *self.dependency_graph_review.summary_lines(),
            "",
            "## Safety assertions",
            "- Transactions sent: no",
            "- Aave Red drills executed: no",
            "- Phase 2B execution enabled: no",
        ]
        output = "\n".join(lines)
        SafetyGuard().assert_safe_report(output)
        return output

    def to_markdown(self) -> str:
        return "# " + self.safe_summary()
