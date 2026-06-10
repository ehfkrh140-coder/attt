from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.evm_readonly_client import LOCAL_FORK_UNAVAILABLE
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard
from evidence.live_fork_evidence import (
    AaveReadOnlyDiscoveryEvidence,
    DependencyGraphReviewEvidence,
    LiveForkEvidencePack,
    LocalForkCheckEvidence,
    TargetManifestReviewEvidence,
    localhost_label,
    root_label,
)
from recon.recon_engine import ReconEngine
from scripts.aave_readonly_discovery import run_discovery
from scripts.check_local_evm_fork import run_check
from scripts.generate_dependency_graph_review import generate_dependency_review, load_target_manifest
from scripts.review_target_manifest import review_manifest
from targets.aave_v3_readonly import AAVE_MAX_RESERVES_DEFAULT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a safe Phase 2A.5 live local fork evidence pack.")
    parser.add_argument("--local-rpc-url", default="http://127.0.0.1:8545")
    parser.add_argument("--root-address", required=True)
    parser.add_argument("--network", default="ethereum")
    parser.add_argument("--fork-block", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--export-target")
    parser.add_argument("--export-dependency-review")
    parser.add_argument("--max-reserves", type=int, default=AAVE_MAX_RESERVES_DEFAULT)
    parser.add_argument("--fixture-readonly", action="store_true", help="Use fixture-backed CI evidence; not live validation.")
    return parser


def _line_value(output: str, prefix: str, default: str = "unknown") -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return default


def _parse_local_fork_check(output: str) -> LocalForkCheckEvidence:
    reachable_value = _line_value(output, "- Local fork reachable", "no")
    safety_status = _line_value(output, "- Safety status", "UNKNOWN")
    notes: list[str] = []
    if LOCAL_FORK_UNAVAILABLE in output:
        notes.append(LOCAL_FORK_UNAVAILABLE)
    if BLOCKED_BY_SAFETY_GUARD in output:
        notes.append(BLOCKED_BY_SAFETY_GUARD)
    return LocalForkCheckEvidence(
        reachable=reachable_value == "yes",
        chain_id=_line_value(output, "- Chain id", "unavailable"),
        client_version_status=_line_value(output, "- Client version", "unavailable"),
        read_only_mode=_line_value(output, "- Read-only mode", "yes") == "yes",
        transactions_enabled=_line_value(output, "- Transactions enabled", "no") == "yes",
        safety_status=safety_status,
        notes=notes,
    )


def _fixture_local_evidence() -> LocalForkCheckEvidence:
    return LocalForkCheckEvidence(
        reachable=False,
        chain_id="fixture",
        client_version_status="fixture",
        read_only_mode=True,
        transactions_enabled=False,
        safety_status="FIXTURE_ONLY",
        notes=["fixture-backed evidence", "live local fork smoke still required"],
    )


def _mark_manifest_evidence_source(path: str | None, *, fixture_readonly: bool) -> None:
    if not path:
        return
    manifest_path = Path(path)
    if not manifest_path.exists():
        return
    data = yaml.safe_load(manifest_path.read_text()) or {}
    data["evidence_source"] = "fixture_readonly" if fixture_readonly else "live_local_readonly"
    sources = list(data.get("deployment_sources", []))
    marker = "fixture_readonly" if fixture_readonly else "live_local_readonly"
    if marker not in sources:
        sources.append(marker)
    data["deployment_sources"] = sources
    manifest_path.write_text(yaml.safe_dump(data, sort_keys=False))


def _aave_evidence_from_manifest(
    target_manifest: str | None,
    *,
    root_address: str,
    discovery_output: str,
) -> AaveReadOnlyDiscoveryEvidence:
    if not target_manifest or not Path(target_manifest).exists():
        return AaveReadOnlyDiscoveryEvidence(
            protocol="aave_v3",
            protocol_twin_mode="evm_fork_twin",
            root_address_label=root_label(root_address),
            discovery_status=_line_value(discovery_output, "- Read-only discovery", "unavailable"),
            core_contracts_count=0,
            reserve_count=0,
            max_reserves_requested=0,
            max_reserves_processed=0,
            truncated=False,
            unresolved_calls=[],
            unresolved_reserve_fields=[],
            watch_items=[],
            selected_drill_recommendations=[],
            recon_hypotheses_count=0,
            execution_gated=True,
            mockarena_fallback=False,
        )
    target_spec, data = load_target_manifest(target_manifest)
    metadata = dict((target_spec.protocol_metadata if target_spec else {}).get("aave_v3", {}))
    core = metadata.get("core_contracts", {}) if isinstance(metadata, dict) else {}
    reserves = metadata.get("reserves", []) if isinstance(metadata, dict) else []
    recon_hypotheses = []
    drill_recommendations: list[str] = []
    if target_spec is not None:
        recon = ReconEngine().run(target_spec)
        recon_hypotheses = recon.risk_hypotheses
        drill_recommendations = list(dict.fromkeys(h.recommended_drill for h in recon_hypotheses))
    return AaveReadOnlyDiscoveryEvidence(
        protocol=str(data.get("protocol_name", "aave_v3")),
        protocol_twin_mode="evm_fork_twin",
        root_address_label=root_label(root_address),
        discovery_status=str(metadata.get("reserve_discovery_status", _line_value(discovery_output, "- Read-only discovery", "unavailable"))),
        core_contracts_count=sum(1 for value in (core or {}).values() if value),
        reserve_count=len(reserves) if isinstance(reserves, list) else 0,
        max_reserves_requested=int(metadata.get("max_reserves_requested", 0) or 0),
        max_reserves_processed=int(metadata.get("max_reserves_processed", 0) or 0),
        truncated=bool(metadata.get("truncated", False)),
        unresolved_calls=list(metadata.get("unresolved_calls", [])),
        unresolved_reserve_fields=list(metadata.get("unresolved_reserve_fields", [])),
        watch_items=list(metadata.get("watch_items", [])),
        selected_drill_recommendations=drill_recommendations,
        recon_hypotheses_count=len(recon_hypotheses),
        execution_gated=True,
        mockarena_fallback=False,
    )


def _dependency_evidence(path: str | None) -> DependencyGraphReviewEvidence:
    if not path:
        return DependencyGraphReviewEvidence("dependency-review", False, 0, 0, 0, 0, 0, "missing")
    review_path = Path(path)
    if not review_path.exists():
        return DependencyGraphReviewEvidence(review_path.name, False, 0, 0, 0, 0, 0, "missing")
    text = review_path.read_text()
    def number(label: str) -> int:
        value = _line_value(text, label, "0")
        try:
            return int(value)
        except ValueError:
            return 0
    return DependencyGraphReviewEvidence(
        review_path=review_path.name,
        exists=True,
        reserve_paths_count=number("- Reserve paths count"),
        debt_paths_count=number("- Debt paths count"),
        reserve_oracle_paths_count=number("- Reserve oracle paths count"),
        watch_items_count=number("- Watch items count"),
        unresolved_items_count=number("- Unresolved reserve fields count"),
        review_status=_line_value(text, "- Review status", "unknown"),
    )


def _missing_prerequisites(
    *,
    fixture_readonly: bool,
    local_fork: LocalForkCheckEvidence,
    target_review: TargetManifestReviewEvidence,
    dependency_review: DependencyGraphReviewEvidence,
    aave: AaveReadOnlyDiscoveryEvidence,
) -> tuple[str, list[str]]:
    missing: list[str] = []
    if fixture_readonly:
        missing.append("live local fork evidence")
    if not local_fork.reachable:
        missing.append("reachable local fork")
    if not target_review.exists:
        missing.append("target manifest candidate")
    if not dependency_review.exists:
        missing.append("dependency graph review candidate")
    if target_review.scope_confirmed:
        missing.append("scope must be review-confirmed outside generated manifest")
    else:
        missing.append("reviewer scope confirmation")
    if aave.discovery_status not in {"fully_discovered", "full"}:
        missing.append("full read-only discovery")
    missing.append("Phase 2B explicit enablement remains absent")
    if fixture_readonly:
        status = "blocked_fixture_only"
    elif missing:
        status = "blocked_missing_prerequisites"
    else:
        status = "review_candidate_only"
    return status, list(dict.fromkeys(missing))


def generate_evidence_pack(
    *,
    local_rpc_url: str,
    root_address: str,
    network: str,
    fork_block: str | None,
    output: str,
    export_target: str | None,
    export_dependency_review: str | None,
    max_reserves: int = AAVE_MAX_RESERVES_DEFAULT,
    fixture_readonly: bool = False,
) -> tuple[LiveForkEvidencePack, str]:
    if not fixture_readonly:
        SafetyGuard().assert_local_rpc(local_rpc_url)
        local_output = run_check(local_rpc_url)
        local_evidence = _parse_local_fork_check(local_output)
    else:
        local_output = "Local EVM Fork Read-only Smoke\n- Safety status: FIXTURE_ONLY"
        local_evidence = _fixture_local_evidence()

    discovery_output = run_discovery(
        root_address=root_address,
        network=network,
        fork_block=fork_block,
        local_rpc_url=local_rpc_url,
        export_target=export_target,
        fixture_readonly=fixture_readonly,
        max_reserves=max_reserves,
    )
    _mark_manifest_evidence_source(export_target, fixture_readonly=fixture_readonly)

    if export_dependency_review:
        if export_target and Path(export_target).exists():
            generate_dependency_review(export_target, export_dependency_review)
        else:
            generate_dependency_review("missing-target-manifest.yaml", export_dependency_review)

    target_review = review_manifest(export_target) if export_target else TargetManifestReviewEvidence(
        manifest_path="target-manifest",
        exists=False,
        scope_confirmed=False,
        authorized_scope=False,
        executable_drills_allowed=False,
        read_only_only=False,
        contract_count=0,
        reserve_count=0,
        has_protocol_metadata=False,
        safety_notes=["manifest_not_requested"],
    )
    dependency_review = _dependency_evidence(export_dependency_review)
    aave_evidence = _aave_evidence_from_manifest(export_target, root_address=root_address, discovery_output=discovery_output)
    candidate_status, missing = _missing_prerequisites(
        fixture_readonly=fixture_readonly,
        local_fork=local_evidence,
        target_review=target_review,
        dependency_review=dependency_review,
        aave=aave_evidence,
    )
    pack = LiveForkEvidencePack.now(
        protocol="aave_v3",
        network=network,
        fork_block=fork_block,
        local_rpc_url_label=localhost_label(local_rpc_url) if not fixture_readonly else "fixture-local-rpc",
        local_fork=local_evidence,
        aave_discovery=aave_evidence,
        target_manifest=target_review,
        dependency_graph_review=dependency_review,
        phase2b_candidate_status=candidate_status,
        missing_prerequisites=missing,
        evidence_source="fixture-backed" if fixture_readonly else ("live-local" if local_evidence.reachable else "live-local-unavailable"),
    )
    evidence_path = Path(output)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = pack.to_markdown()
    evidence_path.write_text(markdown)
    safe_output = pack.safe_summary()
    SafetyGuard().assert_safe_report(local_output + "\n" + discovery_output + "\n" + safe_output)
    return pack, safe_output


def main() -> int:
    args = build_parser().parse_args()
    try:
        _pack, output = generate_evidence_pack(
            local_rpc_url=args.local_rpc_url,
            root_address=args.root_address,
            network=args.network,
            fork_block=args.fork_block,
            output=args.output,
            export_target=args.export_target,
            export_dependency_review=args.export_dependency_review,
            max_reserves=args.max_reserves,
            fixture_readonly=args.fixture_readonly,
        )
    except SafetyGuardError:
        output = "\n".join(
            [
                "Live Fork Evidence Pack",
                f"- Status: {BLOCKED_BY_SAFETY_GUARD}",
                "- Evidence source: blocked",
                "- Transactions sent: no",
                "- Phase 2B candidate status: blocked_by_safety_guard",
            ]
        )
        SafetyGuard().assert_safe_report(output)
        print(output)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
