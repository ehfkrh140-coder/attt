from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.evm_json_rpc_transport import EvmJsonRpcError, EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient, LOCAL_FORK_UNAVAILABLE
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a localhost EVM fork with read-only RPC calls.")
    parser.add_argument("--local-rpc-url", default="http://127.0.0.1:8545")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    lines = ["Local EVM Fork Read-only Smoke"]
    try:
        transport = EvmJsonRpcTransport(args.local_rpc_url)
        client = EvmReadonlyClient(local_rpc_url=args.local_rpc_url, transport=transport)
        chain_id = client.get_chain_id()
        client_version = "unavailable"
        try:
            version = transport.call("web3_clientVersion", [])
            client_version = "available" if version else "unavailable"
        except EvmJsonRpcError:
            client_version = "unavailable"
        lines.extend(
            [
                "- Local fork reachable: yes",
                f"- Chain id: {chain_id}",
                "- Read-only mode: yes",
                "- Transactions enabled: no",
                "- Red drills executed: no",
                f"- Client version probe: {client_version}",
            ]
        )
    except EvmJsonRpcError:
        lines.extend(
            [
                "- Local fork reachable: no",
                f"- Status: {LOCAL_FORK_UNAVAILABLE}",
                "- Read-only mode: yes",
                "- Transactions enabled: no",
                "- Red drills executed: no",
            ]
        )
    except SafetyGuardError:
        lines.extend(
            [
                "- Local fork reachable: blocked",
                f"- Status: {BLOCKED_BY_SAFETY_GUARD}",
                "- Read-only mode: yes",
                "- Transactions enabled: no",
                "- Red drills executed: no",
            ]
        )
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
