from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.safety import SafetyGuard
from evidence.live_fork_evidence import DependencyGraphReviewEvidence
from recon.recon_engine import ReconEngine
from targets.target_schema import TargetProtocolSpec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a safe dependency graph review from a read-only TargetProtocolSpec manifest.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _safe_path_label(path: Path) -> str:
    return path.name if path.name else "dependency-review"


def load_target_manifest(path: str | Path) -> tuple[TargetProtocolSpec | None, dict[str, Any]]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        return None, {}
    data = yaml.safe_load(manifest_path.read_text()) or {}
    target = TargetProtocolSpec(
        protocol_name=data.get("protocol_name", "aave_v3"),
        runtime=data.get("runtime", "evm"),
        network_name=data.get("network_name", "ethereum"),
        fork_block=data.get("fork_block"),
        target_mode=data.get("target_mode", "resolver"),
        deployment_sources=list(data.get("deployment_sources", [])),
        in_scope_contracts=list(data.get("in_scope_contracts", [])),
        out_of_scope_contracts=list(data.get("out_of_scope_contracts", [])),
        critical_assets=list(data.get("critical_assets", [])),
        oracle_sources=list(data.get("oracle_sources", [])),
        dex_dependencies=list(data.get("dex_dependencies", [])),
        governance_contracts=list(data.get("governance_contracts", [])),
        admin_roles=list(data.get("admin_roles", [])),
        protocol_metadata=dict(data.get("protocol_metadata", {})),
        authorized_scope=bool(data.get("authorized_scope", False)),
        scope_confirmed=bool(data.get("scope_confirmed", False)),
    )
    return target, data


def _review_status(data: dict[str, Any], metadata: dict[str, Any]) -> str:
    if not metadata or int(metadata.get("reserve_count", 0) or 0) == 0:
        return "insufficient_metadata"
    if data.get("evidence_source") == "fixture_readonly" or "fixture_readonly" in data.get("deployment_sources", []):
        return "fixture_review_candidate"
    return "live_readonly_review_candidate"


def generate_dependency_review(target: str | Path, output: str | Path) -> tuple[DependencyGraphReviewEvidence, str]:
    target_spec, data = load_target_manifest(target)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if target_spec is None:
        evidence = DependencyGraphReviewEvidence(
            review_path=_safe_path_label(output_path),
            exists=False,
            reserve_paths_count=0,
            debt_paths_count=0,
            reserve_oracle_paths_count=0,
            watch_items_count=0,
            unresolved_items_count=0,
            review_status="insufficient_metadata",
        )
        markdown = render_dependency_review(evidence, [], [], [])
        output_path.write_text(markdown)
        return evidence, markdown
    recon = ReconEngine().run(target_spec)
    dependency_graph = recon.dependency_graph
    metadata = dict(target_spec.protocol_metadata.get("aave_v3", {}))
    watch_items = list(metadata.get("watch_items", []))
    unresolved = list(metadata.get("unresolved_reserve_fields", []))
    drills = list(dict.fromkeys(h.recommended_drill for h in recon.risk_hypotheses))
    evidence = DependencyGraphReviewEvidence(
        review_path=_safe_path_label(output_path),
        exists=True,
        reserve_paths_count=len(dependency_graph.get("reserve_paths", [])),
        debt_paths_count=len(dependency_graph.get("debt_paths", [])),
        reserve_oracle_paths_count=len(dependency_graph.get("reserve_oracle_paths", [])),
        watch_items_count=len(watch_items),
        unresolved_items_count=len(unresolved),
        review_status=_review_status(data, metadata),
    )
    markdown = render_dependency_review(evidence, watch_items, unresolved, drills, contract_nodes_count=len(recon.contract_graph.get("nodes", [])), risk_count=len(recon.risk_hypotheses))
    output_path.write_text(markdown)
    return evidence, markdown


def render_dependency_review(
    evidence: DependencyGraphReviewEvidence,
    watch_items: list[str],
    unresolved: list[str],
    drills: list[str],
    *,
    contract_nodes_count: int = 0,
    risk_count: int = 0,
) -> str:
    gated_drills = [f"{drill} (gated)" for drill in drills]
    lines = [
        "Dependency Graph Review Candidate",
        f"- Review status: {evidence.review_status}",
        f"- Contract nodes count: {contract_nodes_count}",
        f"- Reserve paths count: {evidence.reserve_paths_count}",
        f"- Debt paths count: {evidence.debt_paths_count}",
        f"- Reserve oracle paths count: {evidence.reserve_oracle_paths_count}",
        f"- Watch items count: {evidence.watch_items_count}",
        "- Watch items: " + (", ".join(watch_items) if watch_items else "none"),
        f"- Unresolved reserve fields count: {evidence.unresolved_items_count}",
        "- Unresolved reserve fields: " + (", ".join(unresolved) if unresolved else "none"),
        f"- Risk hypotheses count: {risk_count}",
        "- Drill recommendations gated: " + (", ".join(gated_drills) if gated_drills else "none"),
        "- Scope confirmed by this review: no",
        "- Execution permission granted: no",
        "- Transactions sent: no",
    ]
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    return output


def main() -> int:
    args = build_parser().parse_args()
    _evidence, markdown = generate_dependency_review(args.target, args.output)
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
