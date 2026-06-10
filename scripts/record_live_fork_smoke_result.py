from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "templates" / "MANUAL_LIVE_FORK_SMOKE_RESULT_TEMPLATE.md"
SELECTOR_RE = re.compile(r"(?<![A-Za-z0-9])0x[a-fA-F0-9]{8}(?![a-fA-F0-9])")
LONG_HEX_RE = re.compile(r"(?<![A-Za-z0-9])0x[a-fA-F0-9]{16,}(?![A-Za-z0-9])")


SAFE_FIELD_ORDER = [
    ("date", "Date"),
    ("local_fork_tool", "Local fork tool"),
    ("fork_block", "Fork block"),
    ("local_rpc_url", "Local RPC URL"),
    ("chain_id", "Chain id"),
    ("root_address", "Root address"),
    ("discovery_status", "Discovery status"),
    ("discovered_contracts", "Discovered contracts"),
    ("unresolved_calls", "Unresolved calls"),
    ("notes", "Notes"),
    ("reviewer", "Reviewer"),
    ("no_transaction_sent_confirmation", "No transaction sent confirmation"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record a safe manual live local fork smoke result. No network calls are made."
    )
    parser.add_argument("--output", required=True, help="Markdown result path to write.")
    parser.add_argument("--date", default="")
    parser.add_argument("--local-fork-tool", default="")
    parser.add_argument("--fork-block", default="")
    parser.add_argument("--local-rpc-url", required=True)
    parser.add_argument("--chain-id", default="")
    parser.add_argument("--root-address", default="")
    parser.add_argument("--discovery-status", default="")
    parser.add_argument("--discovered-contracts", default="")
    parser.add_argument("--unresolved-calls", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--no-transaction-sent-confirmation", required=True)
    return parser


def _safe_value(value: str, *, allow_local_url: bool = False, redact_long_hex: bool = False) -> str:
    value = value.strip()
    if SELECTOR_RE.search(value):
        raise SafetyGuardError(BLOCKED_BY_SAFETY_GUARD)
    if redact_long_hex:
        value = LONG_HEX_RE.sub("local-address-redacted", value)
    SafetyGuard().assert_safe_report(value)
    if allow_local_url:
        SafetyGuard().assert_local_rpc(value)
    return value or "not provided"


def build_markdown(fields: dict[str, str]) -> str:
    if not TEMPLATE.exists():
        raise FileNotFoundError("manual live fork smoke template missing")
    lines = ["# Manual Live Fork Smoke Result", ""]
    for key, label in SAFE_FIELD_ORDER:
        lines.append(f"- {label}: {fields[key]}")
    lines.extend(
        [
            "",
            "Safety notes:",
            "- This record is local-read-only evidence only.",
            "- It does not enable fork execution.",
            "- It confirms no transaction was sent during the smoke check.",
        ]
    )
    markdown = "\n".join(lines) + "\n"
    SafetyGuard().assert_safe_report(markdown)
    return markdown


def record_result(args: argparse.Namespace) -> tuple[bool, str]:
    output_path = Path(args.output)
    try:
        fields = {
            "date": _safe_value(args.date),
            "local_fork_tool": _safe_value(args.local_fork_tool),
            "fork_block": _safe_value(args.fork_block),
            "local_rpc_url": _safe_value(args.local_rpc_url, allow_local_url=True),
            "chain_id": _safe_value(args.chain_id),
            "root_address": _safe_value(args.root_address, redact_long_hex=True),
            "discovery_status": _safe_value(args.discovery_status),
            "discovered_contracts": _safe_value(args.discovered_contracts, redact_long_hex=True),
            "unresolved_calls": _safe_value(args.unresolved_calls),
            "notes": _safe_value(args.notes, redact_long_hex=True),
            "reviewer": _safe_value(args.reviewer),
            "no_transaction_sent_confirmation": _safe_value(args.no_transaction_sent_confirmation),
        }
        markdown = build_markdown(fields)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown)
        summary = "\n".join(
            [
                "Manual Live Fork Smoke Result Recorder",
                "- Result written: yes",
                f"- Output path: {output_path}",
                "- Safety status: PASS",
                "- Transactions sent: no",
                "- Fork execution enabled: no",
            ]
        )
        SafetyGuard().assert_safe_report(summary)
        return True, summary
    except (SafetyGuardError, ValueError):
        summary = "\n".join(
            [
                "Manual Live Fork Smoke Result Recorder",
                "- Result written: no",
                f"- Status: {BLOCKED_BY_SAFETY_GUARD}",
                "- Safety status: BLOCKED",
                "- Transactions sent: no",
                "- Fork execution enabled: no",
            ]
        )
        SafetyGuard().assert_safe_report(summary)
        return False, summary


def main() -> int:
    args = build_parser().parse_args()
    ok, summary = record_result(args)
    print(summary)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
