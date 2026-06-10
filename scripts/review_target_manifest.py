from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.safety import SafetyGuard
from evidence.live_fork_evidence import TargetManifestReviewEvidence

FORBIDDEN_MANIFEST_TOKENS = (
    "raw_calldata",
    "calldata:",
    "send_raw_transaction",
    "eth_sendtransaction",
    "eth_sendrawtransaction",
    "account_dot_sign_transaction",
    "mnemonic",
    "seed phrase",
    "infura",
    "alchemy",
    "quicknode",
    "ankr",
    "blastapi",
    "publicnode",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a read-only TargetProtocolSpec manifest without confirming scope.")
    parser.add_argument("--target", required=True, help="Path to the generated read-only target manifest.")
    return parser


def _safe_path_label(path: Path) -> str:
    return path.name if path.name else "target-manifest"


def _unsafe_notes(text: str) -> list[str]:
    lowered = text.lower()
    notes: list[str] = []
    for token in FORBIDDEN_MANIFEST_TOKENS:
        if token in lowered:
            notes.append(f"unsafe_token_{token.replace(':', '').replace('.', '_')}")
    if "https://" in lowered or "http://" in lowered:
        if "http://127.0.0.1" not in lowered and "http://localhost" not in lowered:
            notes.append("non_local_rpc_reference")
    return notes


def review_manifest(target: str | Path) -> TargetManifestReviewEvidence:
    path = Path(target)
    if not path.exists():
        return TargetManifestReviewEvidence(
            manifest_path=_safe_path_label(path),
            exists=False,
            scope_confirmed=False,
            authorized_scope=False,
            executable_drills_allowed=False,
            read_only_only=False,
            contract_count=0,
            reserve_count=0,
            has_protocol_metadata=False,
            safety_notes=["manifest_missing"],
        )
    text = path.read_text()
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return TargetManifestReviewEvidence(
            manifest_path=_safe_path_label(path),
            exists=True,
            scope_confirmed=False,
            authorized_scope=False,
            executable_drills_allowed=False,
            read_only_only=False,
            contract_count=0,
            reserve_count=0,
            has_protocol_metadata=False,
            safety_notes=["manifest_unreadable"],
        )
    metadata = data.get("protocol_metadata") if isinstance(data, dict) else {}
    aave_metadata = metadata.get("aave_v3", {}) if isinstance(metadata, dict) else {}
    reserves = aave_metadata.get("reserves", []) if isinstance(aave_metadata, dict) else []
    notes = _unsafe_notes(text)
    if not data.get("read_only_only", False):
        notes.append("read_only_only_missing")
    if bool(data.get("authorized_scope", False)):
        notes.append("authorized_scope_must_remain_false")
    if bool(data.get("scope_confirmed", False)):
        notes.append("scope_confirmed_must_remain_false_for_review")
    if bool(data.get("executable_drills_allowed", False)):
        notes.append("execution_must_remain_disabled")
    if not isinstance(metadata, dict) or "aave_v3" not in metadata:
        notes.append("protocol_metadata_missing")
    if not isinstance(reserves, list) or not reserves:
        notes.append("reserve_metadata_missing")
    return TargetManifestReviewEvidence(
        manifest_path=_safe_path_label(path),
        exists=True,
        scope_confirmed=bool(data.get("scope_confirmed", False)),
        authorized_scope=bool(data.get("authorized_scope", False)),
        executable_drills_allowed=bool(data.get("executable_drills_allowed", False)),
        read_only_only=bool(data.get("read_only_only", False)),
        contract_count=len(data.get("in_scope_contracts", []) or []),
        reserve_count=len(reserves) if isinstance(reserves, list) else 0,
        has_protocol_metadata=isinstance(metadata, dict) and "aave_v3" in metadata,
        safety_notes=notes,
    )


def render_manifest_review(evidence: TargetManifestReviewEvidence) -> str:
    passed = (
        evidence.exists
        and evidence.read_only_only
        and not evidence.scope_confirmed
        and not evidence.authorized_scope
        and not evidence.executable_drills_allowed
        and evidence.has_protocol_metadata
        and evidence.reserve_count > 0
        and not evidence.safety_notes
    )
    lines = [
        "Target Manifest Review",
        f"- Manifest review: {'PASS' if passed else 'FAIL'}",
        f"- Manifest present: {'yes' if evidence.exists else 'no'}",
        f"- Scope confirmed: {'yes' if evidence.scope_confirmed else 'no'}",
        f"- Authorized scope: {'yes' if evidence.authorized_scope else 'no'}",
        f"- Execution enabled: {'yes' if evidence.executable_drills_allowed else 'no'}",
        f"- Read-only only: {'yes' if evidence.read_only_only else 'no'}",
        f"- Contract count: {evidence.contract_count}",
        f"- Reserve count: {evidence.reserve_count}",
        f"- Protocol metadata: {'present' if evidence.has_protocol_metadata else 'missing'}",
        f"- Safe for Phase 2A review: {'yes' if passed else 'no'}",
        "- Safety notes: " + (", ".join(evidence.safety_notes) if evidence.safety_notes else "none"),
        "- Scope auto-confirmed: no",
        "- Transactions sent: no",
    ]
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    return output


def main() -> int:
    args = build_parser().parse_args()
    print(render_manifest_review(review_manifest(args.target)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
