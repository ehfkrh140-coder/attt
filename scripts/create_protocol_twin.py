from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from reports.report_writer import write_protocol_twin_summary
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS, UNSUPPORTED_PROTOCOL_TWIN


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a local protocol twin manifest or report gated status.")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--network", default="local")
    parser.add_argument("--root-address")
    parser.add_argument("--fork-block", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    protocol = args.protocol.lower()
    if protocol == "mock_lending":
        print(write_protocol_twin_summary(run_auto_simulation_sync(AutoSimulationRequest(protocol="mock_lending"))))
        return
    if protocol == "haedal":
        print(UNSUPPORTED_PROTOCOL_TWIN)
        print(write_protocol_twin_summary(run_auto_simulation_sync(AutoSimulationRequest(protocol="haedal", network=args.network))))
        return
    if protocol == "aave_v3" and not args.root_address:
        print(MISSING_PROTOCOL_ROOT_ADDRESS)
        print(write_protocol_twin_summary(run_auto_simulation_sync(AutoSimulationRequest(protocol="aave_v3", network=args.network, fork_block=args.fork_block))))
        return
    if protocol == "aave_v3":
        result = run_auto_simulation_sync(
            AutoSimulationRequest(
                protocol="aave_v3",
                network=args.network,
                root_address=args.root_address,
                fork_block=args.fork_block,
            )
        )
        generated = Path("targets/generated")
        generated.mkdir(parents=True, exist_ok=True)
        path = generated / f"aave_v3_{args.network}_fork.yaml"
        manifest = {
            "protocol_name": "aave_v3",
            "runtime": "evm",
            "network_name": args.network,
            "fork_block": args.fork_block,
            "target_mode": "resolver",
            "deployment_sources": ["local_evm_fork_twin"],
            "in_scope_contracts": [{"name": "PoolAddressesProvider", "address": args.root_address, "category": "admin_config"}],
            "authorized_scope": False,
            "scope_confirmed": False,
        }
        path.write_text(yaml.safe_dump(manifest, sort_keys=False))
        print("TARGET_MANIFEST_CREATED")
        print(f"Target manifest: {path}")
        print(write_protocol_twin_summary(result))
        return
    print(UNSUPPORTED_PROTOCOL_TWIN)


if __name__ == "__main__":
    main()
