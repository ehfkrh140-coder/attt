from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arenas.evm_fork_execution_arena import EvmForkExecutionArena, UNSUPPORTED_EXECUTABLE_FORK_DRILLS
from core.fork_execution_policy import ForkExecutionMode, default_fork_execution_mode
from core.safety import SafetyGuard
from redteam.local_tx_intent import LocalTxIntent

ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check review-only Phase 2B prerequisites without enabling fork execution."
    )
    parser.add_argument("--manual-smoke-result", default="docs/manual_live_fork_smoke_result.md")
    parser.add_argument("--evidence-pack", default="docs/live_fork_evidence/aave_v3_evidence_pack.md")
    parser.add_argument("--target-manifest", default="targets/generated/aave_v3_readonly.yaml")
    parser.add_argument("--dependency-graph-review", default="docs/dependency_graph_review.md")
    parser.add_argument(
        "--reviewer-confirms-scope",
        action="store_true",
        help="A reviewer has explicitly confirmed scope in a separate review artifact.",
    )
    return parser


def _line_value(text: str, prefix: str, default: str = "unknown") -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return default


def _read_evidence_pack(path: Path) -> tuple[bool, str, str, list[str]]:
    if not path.exists():
        return False, "missing", "missing", ["evidence pack missing"]
    text = path.read_text()
    source = _line_value(text, "- Evidence source", "unknown")
    candidate_status = _line_value(text, "- Phase 2B candidate status", "unknown")
    notes: list[str] = []
    if "fixture-backed" in source or "fixture" in candidate_status:
        notes.append("fixture-backed evidence is not enough for Phase 2B execution")
    if "live-local" not in source:
        notes.append("live local evidence not present")
    if "Aave Red drills executed: no" not in text:
        notes.append("evidence must record no Aave Red drills")
    return True, source, candidate_status, notes


def _target_scope_ok(path: Path, reviewer_confirms_scope: bool) -> tuple[bool, str]:
    if not path.exists():
        return False, "target manifest missing"
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return False, "target manifest unreadable"
    if bool(data.get("executable_drills_allowed", False)):
        return False, "target manifest must not allow executable drills"
    if bool(data.get("authorized_scope", False)):
        return False, "target manifest must remain unauthorized until review"
    scope_confirmed = bool(data.get("scope_confirmed", False))
    if scope_confirmed and not reviewer_confirms_scope:
        return False, "target manifest scope requires explicit reviewer confirmation"
    if not scope_confirmed and not reviewer_confirms_scope:
        return False, "target manifest scope unconfirmed"
    return True, "target manifest review gate acknowledged"


def _check_execution_still_disabled() -> tuple[bool, bool]:
    dummy_intent = LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-preflight-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="phase2b-preflight",
    )
    execution_disabled = default_fork_execution_mode() == ForkExecutionMode.DISABLED
    raises_unsupported = False
    try:
        EvmForkExecutionArena().execute_local_intent(dummy_intent)
    except RuntimeError as exc:
        raises_unsupported = str(exc) == UNSUPPORTED_EXECUTABLE_FORK_DRILLS
    return execution_disabled, raises_unsupported


def run_preflight(
    manual_smoke_result: str,
    target_manifest: str,
    dependency_graph_review: str,
    reviewer_confirms_scope: bool = False,
    evidence_pack: str = "docs/live_fork_evidence/aave_v3_evidence_pack.md",
) -> str:
    missing: list[str] = []
    manual_path = Path(manual_smoke_result)
    target_path = Path(target_manifest)
    review_path = Path(dependency_graph_review)
    evidence_path = Path(evidence_pack)

    evidence_exists, evidence_source, candidate_status, evidence_notes = _read_evidence_pack(evidence_path)
    if not evidence_exists:
        missing.append("evidence pack")
    missing.extend(evidence_notes)

    if not manual_path.exists():
        missing.append("manual live fork smoke result")

    target_ok, target_note = _target_scope_ok(target_path, reviewer_confirms_scope)
    if not target_ok:
        missing.append(target_note)

    if not review_path.exists():
        missing.append("dependency graph review")

    checklist_path = ROOT / "docs" / "PHASE_2B_READINESS_CHECKLIST.md"
    checklist_text = checklist_path.read_text() if checklist_path.exists() else ""
    checklist_not_all_checked = "- [ ]" in checklist_text
    if not checklist_not_all_checked:
        missing.append("readiness checklist must not be fully checked by default")

    execution_disabled, raises_unsupported = _check_execution_still_disabled()
    if not execution_disabled:
        missing.append("fork execution mode must remain disabled")
    if not raises_unsupported:
        missing.append("fork execution arena must remain unsupported")

    missing = list(dict.fromkeys(missing))
    review_ready = (
        not missing
        and evidence_source == "live-local"
        and manual_path.exists()
        and target_path.exists()
        and review_path.exists()
        and reviewer_confirms_scope
        and execution_disabled
        and raises_unsupported
    )
    lines = [
        "Phase 2B Preflight",
        f"- Phase 2B readiness: {'REVIEW_READY' if review_ready else 'FAIL'}",
        "- Execution enabled: no",
        f"- Fork execution disabled: {'yes' if execution_disabled else 'no'}",
        f"- Execution arena unsupported: {'yes' if raises_unsupported else 'no'}",
        f"- Evidence pack: {'present' if evidence_exists else 'missing'}",
        f"- Evidence source: {evidence_source}",
        f"- Evidence quality: {candidate_status}",
        f"- Manual live fork smoke result: {'present' if manual_path.exists() else 'missing'}",
        f"- Target manifest: {'present' if target_path.exists() else 'missing'}",
        f"- Target manifest note: {target_note}",
        f"- Dependency graph review: {'present' if review_path.exists() else 'missing'}",
        f"- Checklist not fully checked by default: {'yes' if checklist_not_all_checked else 'no'}",
        "- Fixture-backed evidence sufficient for execution: no",
        "- Transactions sent: no",
        "- Executable fork drills enabled: no",
        "- Missing prerequisites: " + (", ".join(missing) if missing else "none"),
    ]
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    return output


def main() -> int:
    args = build_parser().parse_args()
    print(
        run_preflight(
            args.manual_smoke_result,
            args.target_manifest,
            args.dependency_graph_review,
            args.reviewer_confirms_scope,
            args.evidence_pack,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
