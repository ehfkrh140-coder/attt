from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml

from adapters.evm_json_rpc_transport import EvmJsonRpcError, EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient, LOCAL_FORK_UNAVAILABLE
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard
from recon.recon_engine import ReconEngine
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest
from targets.target_schema import TargetProtocolSpec

TransportFactory = Callable[[str], EvmJsonRpcTransport]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe Aave V3 read-only discovery against a localhost EVM fork.")
    parser.add_argument("--root-address")
    parser.add_argument("--network", default="ethereum")
    parser.add_argument("--fork-block", default=None)
    parser.add_argument("--local-rpc-url", default="http://127.0.0.1:8545")
    parser.add_argument("--export-target")
    parser.add_argument("--fixture-readonly", action="store_true", help=argparse.SUPPRESS)
    return parser


def _fixture_client(root_address: str) -> EvmReadonlyClient:
    return EvmReadonlyClient(
        local_rpc_url="mock://fixture",
        call_results={
            (root_address.lower(), "aave_provider_get_pool"): "aave://pool",
            (root_address.lower(), "aave_provider_get_pool_configurator"): "aave://pool-configurator",
            (root_address.lower(), "aave_provider_get_price_oracle"): "aave://price-oracle",
            (root_address.lower(), "aave_provider_get_acl_manager"): "aave://acl-manager",
            ("aave://pool", "aave_pool_get_reserves_list"): ["aave://usdc", "aave://weth"],
            ("aave://pool", "aave_pool_get_reserve_data", "aave://usdc"): {
                "asset": "aave://usdc",
                "symbol": "USDC",
                "a_token": "aave://ausdc",
                "stable_debt_token": "aave://stable-debt-usdc",
                "variable_debt_token": "aave://variable-debt-usdc",
                "interest_rate_strategy": "aave://rate-strategy-usdc",
                "decimals": 6,
                "ltv_bps": 8000,
                "liquidation_threshold_bps": 8500,
                "borrowing_enabled": True,
                "stable_borrow_enabled": False,
                "active": True,
                "frozen": False,
            },
            ("aave://pool", "aave_pool_get_reserve_data", "aave://weth"): {
                "asset": "aave://weth",
                "symbol": "WETH",
                "a_token": "aave://aweth",
                "stable_debt_token": "aave://stable-debt-weth",
                "variable_debt_token": "aave://variable-debt-weth",
                "interest_rate_strategy": "aave://rate-strategy-weth",
                "decimals": 18,
                "ltv_bps": 8250,
                "liquidation_threshold_bps": 8600,
                "borrowing_enabled": True,
                "stable_borrow_enabled": False,
                "active": True,
                "frozen": False,
            },
        },
    )


def _target_manifest(target: TargetProtocolSpec) -> dict[str, object]:
    return {
        "protocol_name": target.protocol_name,
        "runtime": target.runtime,
        "network_name": target.network_name,
        "fork_block": target.fork_block,
        "target_mode": target.target_mode,
        "deployment_sources": target.deployment_sources,
        "in_scope_contracts": target.in_scope_contracts,
        "out_of_scope_contracts": target.out_of_scope_contracts,
        "critical_assets": target.critical_assets,
        "oracle_sources": target.oracle_sources,
        "dex_dependencies": target.dex_dependencies,
        "governance_contracts": target.governance_contracts,
        "admin_roles": target.admin_roles,
        "protocol_metadata": target.protocol_metadata,
        "authorized_scope": False,
        "scope_confirmed": False,
        "executable_drills_allowed": False,
    }


def _export_target(path: str, target: TargetProtocolSpec) -> str:
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(yaml.safe_dump(_target_manifest(target), sort_keys=False))
    return str(export_path)


def _display_discovery_status(status: str) -> str:
    return {
        "fully_discovered": "full",
        "partially_discovered": "partial",
        "missing_root": "missing-root",
    }.get(status, status)


def _print_safe(lines: list[str]) -> int:
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    print(output)
    return 0


def run_discovery(
    *,
    root_address: str | None,
    network: str = "ethereum",
    fork_block: str | int | None = None,
    local_rpc_url: str = "http://127.0.0.1:8545",
    export_target: str | None = None,
    fixture_readonly: bool = False,
    transport_factory: TransportFactory = EvmJsonRpcTransport,
) -> str:
    lines = ["Aave V3 Read-only Discovery Smoke", "- Protocol: aave_v3", "- Protocol Twin mode: evm_fork_twin"]
    if not root_address:
        lines.extend(
            [
                f"- Status: {MISSING_PROTOCOL_ROOT_ADDRESS}",
                "- Read-only discovery: missing-root",
                "- Recon risk hypotheses count: 0",
                "- Executable drills ran: no",
                "- Execution gated: yes",
                "- MockArena fallback: no",
            ]
        )
        output = "\n".join(lines)
        SafetyGuard().assert_safe_report(output)
        return output

    try:
        if fixture_readonly:
            client = _fixture_client(root_address)
        else:
            transport = transport_factory(local_rpc_url)
            client = EvmReadonlyClient(local_rpc_url=local_rpc_url, transport=transport)
            client.get_chain_id()
    except EvmJsonRpcError:
        lines.extend(
            [
                "- Local fork reachable: no",
                f"- Status: {LOCAL_FORK_UNAVAILABLE}",
                "- Read-only discovery: unavailable",
                "- Recon risk hypotheses count: 0",
                "- Executable drills ran: no",
                "- Execution gated: yes",
                "- MockArena fallback: no",
            ]
        )
        output = "\n".join(lines)
        SafetyGuard().assert_safe_report(output)
        return output
    except SafetyGuardError:
        lines.extend(
            [
                "- Local fork reachable: blocked",
                f"- Status: {BLOCKED_BY_SAFETY_GUARD}",
                "- Read-only discovery: unavailable",
                "- Recon risk hypotheses count: 0",
                "- Executable drills ran: no",
                "- Execution gated: yes",
                "- MockArena fallback: no",
            ]
        )
        output = "\n".join(lines)
        SafetyGuard().assert_safe_report(output)
        return output

    resolution = AaveV3Resolver().resolve(
        ProtocolResolutionRequest(
            protocol="aave_v3",
            network=network,
            root_address=root_address,
            fork_block=fork_block,
        ),
        client,
    )
    assert resolution.target is not None
    recon = ReconEngine().run(resolution.target)
    categories = sorted({str(contract.get("category")) for contract in resolution.target.in_scope_contracts})
    contracts = [f"{contract.get('name')}:{contract.get('category')}" for contract in resolution.target.in_scope_contracts]
    unresolved = sorted(note for note in resolution.notes if note.startswith("unresolved_"))
    metadata = resolution.target.protocol_metadata.get("aave_v3", {})
    reserves = metadata.get("reserves", []) if isinstance(metadata, dict) else []
    reserve_symbols = [str(reserve.get("symbol", "unknown")) for reserve in reserves if isinstance(reserve, dict)]
    reserve_status = str(metadata.get("reserve_discovery_status", "unavailable")) if isinstance(metadata, dict) else "unavailable"
    drills = [hypothesis.recommended_drill for hypothesis in recon.risk_hypotheses]
    exported = "no"
    if export_target:
        exported = _export_target(export_target, resolution.target)
    lines.extend(
        [
            "- Local fork reachable: yes",
            f"- Read-only discovery: {_display_discovery_status(resolution.discovery_status)}",
            "- Executable drills ran: no",
            "- Execution gated: yes",
            "- MockArena fallback: no",
            f"- Discovered contract categories: {', '.join(categories) if categories else 'none'}",
            f"- Discovered contracts: {', '.join(contracts) if contracts else 'none'}",
            f"- Unresolved calls: {', '.join(unresolved) if unresolved else 'none'}",
            f"- Reserve discovery: {reserve_status}",
            f"- Reserve count: {len(reserves)}",
            f"- Reserve symbols: {', '.join(reserve_symbols) if reserve_symbols else 'none'}",
            f"- Selected drill recommendations: {', '.join(drills) if drills else 'none'}",
            f"- Recon risk hypotheses count: {len(recon.risk_hypotheses)}",
            "- Twin Fidelity Score: read-only-local-fork",
            "- Unsupported components: executable_evm_adapter",
            f"- Exported target manifest: {exported}",
        ]
    )
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    return output


def main() -> int:
    args = build_parser().parse_args()
    print(
        run_discovery(
            root_address=args.root_address,
            network=args.network,
            fork_block=args.fork_block,
            local_rpc_url=args.local_rpc_url,
            export_target=args.export_target,
            fixture_readonly=args.fixture_readonly,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
