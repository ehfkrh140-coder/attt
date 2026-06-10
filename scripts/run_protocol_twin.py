from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from reports.report_writer import write_protocol_twin_summary
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from targets.target_schema import TargetProtocolSpec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe local Protocol Twin simulation.")
    parser.add_argument("--protocol")
    parser.add_argument("--network", default="local")
    parser.add_argument("--fork-block", default=None)
    parser.add_argument("--root-address")
    parser.add_argument("--local-rpc-url", default="http://127.0.0.1:8545")
    parser.add_argument("--target")
    parser.add_argument("--fixture-readonly", action="store_true", help=argparse.SUPPRESS)
    return parser


def _target_from_yaml(path: Path) -> TargetProtocolSpec:
    data = yaml.safe_load(path.read_text())
    return TargetProtocolSpec(
        protocol_name=data["protocol_name"],
        runtime=data["runtime"],
        network_name=data["network_name"],
        fork_block=data.get("fork_block"),
        target_mode=data.get("target_mode", "resolver"),
        deployment_sources=data.get("deployment_sources", []),
        in_scope_contracts=data.get("in_scope_contracts", []),
        out_of_scope_contracts=data.get("out_of_scope_contracts", []),
        critical_assets=data.get("critical_assets", []),
        oracle_sources=data.get("oracle_sources", []),
        dex_dependencies=data.get("dex_dependencies", []),
        governance_contracts=data.get("governance_contracts", []),
        admin_roles=data.get("admin_roles", []),
        authorized_scope=bool(data.get("authorized_scope", False)),
        scope_confirmed=bool(data.get("scope_confirmed", False)),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.target:
        result = run_auto_simulation_sync(AutoSimulationRequest(target=_target_from_yaml(Path(args.target))))
    else:
        result = run_auto_simulation_sync(
            AutoSimulationRequest(
                protocol=args.protocol or "mock_lending",
                network=args.network,
                fork_block=args.fork_block,
                root_address=args.root_address,
                local_rpc_url=args.local_rpc_url,
                fixture_readonly=args.fixture_readonly,
            )
        )
    print(write_protocol_twin_summary(result))


if __name__ == "__main__":
    main()
