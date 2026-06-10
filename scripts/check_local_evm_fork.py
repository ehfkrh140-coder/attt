from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.evm_json_rpc_transport import EvmJsonRpcError, EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient, LOCAL_FORK_UNAVAILABLE
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard

TransportFactory = Callable[[str], EvmJsonRpcTransport]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a localhost EVM fork with read-only RPC calls.")
    parser.add_argument("--local-rpc-url", default="http://127.0.0.1:8545")
    return parser


def run_check(local_rpc_url: str, transport_factory: TransportFactory = EvmJsonRpcTransport) -> str:
    lines = ["Local EVM Fork Read-only Smoke"]
    try:
        transport = transport_factory(local_rpc_url)
        client = EvmReadonlyClient(local_rpc_url=local_rpc_url, transport=transport)
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
                f"- Client version: {client_version}",
                "- Read-only mode: yes",
                "- Transactions enabled: no",
                "- Red drills executed: no",
                "- Safety status: PASS",
            ]
        )
    except EvmJsonRpcError:
        lines.extend(
            [
                "- Local fork reachable: no",
                f"- Status: {LOCAL_FORK_UNAVAILABLE}",
                "- Chain id: unavailable",
                "- Client version: unavailable",
                "- Read-only mode: yes",
                "- Transactions enabled: no",
                "- Red drills executed: no",
                "- Safety status: UNAVAILABLE",
            ]
        )
    except SafetyGuardError:
        lines.extend(
            [
                "- Local fork reachable: blocked",
                f"- Status: {BLOCKED_BY_SAFETY_GUARD}",
                "- Chain id: blocked",
                "- Client version: blocked",
                "- Read-only mode: yes",
                "- Transactions enabled: no",
                "- Red drills executed: no",
                "- Safety status: BLOCKED",
            ]
        )
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    return output


def main() -> int:
    args = build_parser().parse_args()
    print(run_check(args.local_rpc_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
