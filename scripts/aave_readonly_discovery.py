from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.evm_json_rpc_transport import EvmJsonRpcError, EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient, LOCAL_FORK_UNAVAILABLE
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard
from recon.recon_engine import ReconEngine
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe Aave V3 read-only discovery against a localhost EVM fork.")
    parser.add_argument("--root-address")
    parser.add_argument("--network", default="ethereum")
    parser.add_argument("--fork-block", default=None)
    parser.add_argument("--local-rpc-url", default="http://127.0.0.1:8545")
    return parser


def _print_safe(lines: list[str]) -> int:
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    print(output)
    return 0


def main() -> int:
    args = build_parser().parse_args()
    lines = ["Aave V3 Read-only Discovery Smoke", "- Protocol Twin mode: evm_fork_twin"]
    if not args.root_address:
        return _print_safe(
            lines
            + [
                f"- Status: {MISSING_PROTOCOL_ROOT_ADDRESS}",
                "- Read-only discovery: no",
                "- Executable drills ran: no",
                "- Execution gated: yes",
                "- MockArena fallback: no",
            ]
        )
    try:
        transport = EvmJsonRpcTransport(args.local_rpc_url)
        client = EvmReadonlyClient(local_rpc_url=args.local_rpc_url, transport=transport)
        client.get_chain_id()
    except EvmJsonRpcError:
        return _print_safe(
            lines
            + [
                "- Local fork reachable: no",
                f"- Status: {LOCAL_FORK_UNAVAILABLE}",
                "- Read-only discovery: unavailable",
                "- Executable drills ran: no",
                "- Execution gated: yes",
                "- MockArena fallback: no",
            ]
        )
    except SafetyGuardError:
        return _print_safe(
            lines
            + [
                "- Local fork reachable: blocked",
                f"- Status: {BLOCKED_BY_SAFETY_GUARD}",
                "- Read-only discovery: no",
                "- Executable drills ran: no",
                "- Execution gated: yes",
                "- MockArena fallback: no",
            ]
        )

    resolution = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(
            protocol="aave_v3",
            network=args.network,
            root_address=args.root_address,
            fork_block=args.fork_block,
        ),
        client,
    )
    assert resolution.target is not None
    recon = ReconEngine().run(resolution.target)
    categories = sorted({str(contract.get("category")) for contract in resolution.target.in_scope_contracts})
    unresolved = sorted(note for note in resolution.notes if note.startswith("unresolved_"))
    discovery = "partial" if unresolved else "yes"
    drills = [hypothesis.recommended_drill for hypothesis in recon.risk_hypotheses]
    return _print_safe(
        lines
        + [
            "- Local fork reachable: yes",
            f"- Read-only discovery: {discovery}",
            "- Executable drills ran: no",
            "- Execution gated: yes",
            "- MockArena fallback: no",
            f"- Discovered contract categories: {', '.join(categories) if categories else 'none'}",
            f"- Unresolved calls: {', '.join(unresolved) if unresolved else 'none'}",
            f"- Selected drill recommendations: {', '.join(drills) if drills else 'none'}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
