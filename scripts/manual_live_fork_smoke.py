from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.safety import SafetyGuard
from scripts.aave_readonly_discovery import run_discovery
from scripts.check_local_evm_fork import run_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Optional manual Phase 2A smoke for a user-started localhost EVM fork. Not used by CI."
    )
    parser.add_argument("--local-rpc-url", required=True, help="Must be localhost or 127.0.0.1.")
    parser.add_argument("--root-address", required=True, help="Aave V3 PoolAddressesProvider/root address on the local fork.")
    parser.add_argument("--network", default="ethereum")
    parser.add_argument("--fork-block", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    fork_output = run_check(args.local_rpc_url)
    discovery_output = run_discovery(
        root_address=args.root_address,
        network=args.network,
        fork_block=args.fork_block,
        local_rpc_url=args.local_rpc_url,
    )
    output = "\n".join(
        [
            "Manual Live Local Fork Smoke",
            "- Optional manual check: yes",
            "- CI default: not run",
            "- Transactions sent: no",
            "- Red drills executed: no",
            fork_output,
            discovery_output,
        ]
    )
    SafetyGuard().assert_safe_report(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
