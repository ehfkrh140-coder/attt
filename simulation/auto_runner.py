from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from adapters.evm_json_rpc_transport import EvmJsonRpcError, EvmJsonRpcTransport
from adapters.evm_readonly_client import EvmReadonlyClient, LOCAL_FORK_UNAVAILABLE
from environment.environment_builder import EnvironmentTwin, EnvironmentTwinBuilder
from environment.fidelity import TwinFidelityScore, score_twin_fidelity
from eval.regression_suite import CORE_REGRESSION_MODES, run_core_regression_suite
from eval.scoring import ScoreCard, default_safety_score, score_evaluation_quality, score_recon_report, score_red_drills
from recon.recon_engine import ReconEngine, ReconReport
from redteam.drill_planner import plan_drills
from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS, ProtocolCatalog, UNSUPPORTED_PROTOCOL_TWIN
from targets.protocol_resolvers.aave_v3 import AaveV3Resolver
from targets.protocol_resolvers.base import ProtocolResolutionRequest, ProtocolResolutionResult
from targets.protocol_resolvers.sui_gated import SuiGatedResolver
from targets.target_schema import TargetProtocolSpec, mock_target


@dataclass(frozen=True)
class AutoSimulationRequest:
    protocol: str = "mock_lending"
    network: str = "local"
    fork_block: str | int | None = None
    root_address: str | None = None
    local_rpc_url: str = "http://127.0.0.1:8545"
    explicit_mock: bool = False
    target: TargetProtocolSpec | None = None
    fixture_readonly: bool = False


@dataclass(frozen=True)
class AutoSimulationResult:
    status: str
    protocol: str
    protocol_twin_mode: str
    runtime: str
    environment_twin: EnvironmentTwin | None
    twin_fidelity: TwinFidelityScore
    scorecard: ScoreCard | None
    recon_report: ReconReport | None
    selected_drills: list[str]
    executable_drills_ran: bool
    regression_case_count: int
    modes_tested: list[str]
    unsupported_components: list[str] = field(default_factory=list)
    resolution: ProtocolResolutionResult | None = None
    read_only_discovery: str = "no"
    discovered_contracts: list[str] = field(default_factory=list)

    def safe_summary_lines(self) -> list[str]:
        return [
            f"- Protocol: {self.protocol}",
            f"- Protocol Twin mode: {self.protocol_twin_mode}",
            f"- Result mode: {self.status}",
            f"- Twin Fidelity Score: {self.twin_fidelity.overall:.2f}",
            f"- Environment Twin coverage: orderflow={self.twin_fidelity.orderflow_coverage:.2f}, keeper={self.twin_fidelity.keeper_coverage:.2f}, oracle={self.twin_fidelity.oracle_update_coverage:.2f}, liquidity={self.twin_fidelity.liquidity_coverage:.2f}",
            f"- Unsupported components: {', '.join(self.unsupported_components) if self.unsupported_components else 'none'}",
            f"- Executable drills ran: {'yes' if self.executable_drills_ran else 'no'}",
        ]


class AutoSimulationRunner:
    def __init__(self, catalog: ProtocolCatalog | None = None) -> None:
        self.catalog = catalog or ProtocolCatalog()
        self.environment_builder = EnvironmentTwinBuilder()

    async def run(self, request: AutoSimulationRequest) -> AutoSimulationResult:
        if request.target is not None:
            return await self._run_target(request.target)
        protocol = request.protocol.lower()
        entry = self.catalog.get(protocol)
        if protocol == "mock_lending":
            return await self._run_mock_lending()
        if protocol == "aave_v3":
            return self._run_aave_readonly_or_gated(request, entry.twin_mode, entry.runtime)
        if protocol == "haedal":
            return self._unsupported_sui(request, entry.twin_mode, entry.runtime)
        return self._unsupported(protocol, "unknown", "unknown", [UNSUPPORTED_PROTOCOL_TWIN])

    async def _run_target(self, target: TargetProtocolSpec) -> AutoSimulationResult:
        if target.runtime == "mock":
            return await self._run_mock_lending(target)
        unsupported = ["executable_adapter_not_ready"]
        environment = self.environment_builder.build()
        recon = ReconEngine().run(target)
        fidelity = score_twin_fidelity("evm_fork_twin" if target.runtime == "evm" else "sui_state_twin", environment, unsupported)
        return AutoSimulationResult(
            status="readonly_or_gated_execution",
            protocol=target.protocol_name,
            protocol_twin_mode="evm_fork_twin" if target.runtime == "evm" else "sui_state_twin",
            runtime=target.runtime,
            environment_twin=environment,
            twin_fidelity=fidelity,
            scorecard=None,
            recon_report=recon,
            selected_drills=[hypothesis.recommended_drill for hypothesis in recon.risk_hypotheses],
            executable_drills_ran=False,
            regression_case_count=0,
            modes_tested=[],
            unsupported_components=unsupported,
        )

    async def _run_mock_lending(self, target: TargetProtocolSpec | None = None) -> AutoSimulationResult:
        target = target or mock_target(True)
        environment = self.environment_builder.build()
        recon = ReconEngine().run(target)
        selected = [drill.__class__.__name__ for drill in plan_drills(recon.risk_hypotheses)]
        regression = await run_core_regression_suite()
        fidelity = score_twin_fidelity("mockarena", environment, [])
        return AutoSimulationResult(
            status="mockarena_executable",
            protocol="mock_lending",
            protocol_twin_mode="mockarena",
            runtime="mock",
            environment_twin=environment,
            twin_fidelity=fidelity,
            scorecard=regression.scorecard,
            recon_report=recon,
            selected_drills=selected,
            executable_drills_ran=True,
            regression_case_count=len(regression.cases),
            modes_tested=list(CORE_REGRESSION_MODES),
        )

    def _run_aave_readonly_or_gated(self, request: AutoSimulationRequest, twin_mode: str, runtime: str) -> AutoSimulationResult:
        resolver = AaveV3Resolver(self.catalog)
        readonly_client = None
        if request.root_address and request.fixture_readonly:
            readonly_client = EvmReadonlyClient(
                local_rpc_url="mock://fixture",
                chain_id=31337,
                call_results={
                    (request.root_address.lower(), "aave_provider_get_pool"): "aave://pool",
                    (request.root_address.lower(), "aave_provider_get_pool_configurator"): "aave://pool-configurator",
                    (request.root_address.lower(), "aave_provider_get_price_oracle"): "aave://price-oracle",
                    (request.root_address.lower(), "aave_provider_get_acl_manager"): "aave://acl-manager",
                },
            )
        elif request.root_address:
            try:
                transport = EvmJsonRpcTransport(request.local_rpc_url)
                readonly_client = EvmReadonlyClient(
                    local_rpc_url=request.local_rpc_url,
                    chain_id=31337,
                    transport=transport,
                )
                readonly_client.get_chain_id()
            except EvmJsonRpcError:
                return self._aave_unavailable(request, twin_mode, runtime, LOCAL_FORK_UNAVAILABLE)
            except SafetyGuardError:
                return self._aave_unavailable(request, twin_mode, runtime, BLOCKED_BY_SAFETY_GUARD)
        resolution = resolver.resolve(
            ProtocolResolutionRequest(
                protocol="aave_v3",
                network=request.network,
                root_address=request.root_address,
                fork_block=request.fork_block,
            ),
            readonly_client,
        )
        environment = self.environment_builder.build()
        if resolution.error_code == MISSING_PROTOCOL_ROOT_ADDRESS:
            fidelity = score_twin_fidelity(twin_mode, environment, [MISSING_PROTOCOL_ROOT_ADDRESS, "executable_evm_adapter"])
            return AutoSimulationResult(
                status=MISSING_PROTOCOL_ROOT_ADDRESS,
                protocol="aave_v3",
                protocol_twin_mode=twin_mode,
                runtime=runtime,
                environment_twin=environment,
                twin_fidelity=fidelity,
                scorecard=None,
                recon_report=None,
                selected_drills=[],
                executable_drills_ran=False,
                regression_case_count=0,
                modes_tested=[],
                unsupported_components=[MISSING_PROTOCOL_ROOT_ADDRESS, "executable_evm_adapter"],
                resolution=resolution,
                read_only_discovery="no",
            )
        assert resolution.target is not None
        recon = ReconEngine().run(resolution.target)
        selected = [hypothesis.recommended_drill for hypothesis in recon.risk_hypotheses]
        unsupported = ["executable_evm_adapter"]
        fidelity = score_twin_fidelity(twin_mode, environment, unsupported)
        scorecard = ScoreCard(
            recon=score_recon_report(recon),
            red=score_red_drills(selected, blind_compliant=True, impacts_invariants=False),
            blue=run_zero_blue_score(),
            safety=default_safety_score(),
            evaluation=score_evaluation_quality(
                state_diff_used=True,
                invariants_used=True,
                multi_mode_ordering_used=False,
                damage_recording_honest=True,
                defense_first_not_overweighted=True,
                label_leakage_checked=True,
            ),
        )
        return AutoSimulationResult(
            status="evm_readonly_fork_twin_execution_gated",
            protocol="aave_v3",
            protocol_twin_mode=twin_mode,
            runtime=runtime,
            environment_twin=environment,
            twin_fidelity=fidelity,
            scorecard=scorecard,
            recon_report=recon,
            selected_drills=selected,
            executable_drills_ran=False,
            regression_case_count=0,
            modes_tested=[],
            unsupported_components=unsupported,
            resolution=resolution,
            read_only_discovery=resolution.discovery_status,
            discovered_contracts=[f"{contract.get('name')}:{contract.get('category')}" for contract in resolution.target.in_scope_contracts],
        )

    def _aave_unavailable(
        self,
        request: AutoSimulationRequest,
        twin_mode: str,
        runtime: str,
        status: str,
    ) -> AutoSimulationResult:
        environment = self.environment_builder.build()
        unsupported = [status, "executable_evm_adapter"]
        fidelity = score_twin_fidelity(twin_mode, environment, unsupported)
        return AutoSimulationResult(
            status=status,
            protocol="aave_v3",
            protocol_twin_mode=twin_mode,
            runtime=runtime,
            environment_twin=environment,
            twin_fidelity=fidelity,
            scorecard=None,
            recon_report=None,
            selected_drills=[],
            executable_drills_ran=False,
            regression_case_count=0,
            modes_tested=[],
            unsupported_components=unsupported,
            read_only_discovery="no",
        )

    def _unsupported_sui(self, request: AutoSimulationRequest, twin_mode: str, runtime: str) -> AutoSimulationResult:
        resolver = SuiGatedResolver()
        resolution = resolver.resolve(ProtocolResolutionRequest(protocol=request.protocol, network=request.network))
        return self._unsupported(request.protocol, twin_mode, runtime, ["sui_state_twin_adapter"], resolution)

    def _unsupported(
        self,
        protocol: str,
        twin_mode: str,
        runtime: str,
        unsupported: list[str],
        resolution: ProtocolResolutionResult | None = None,
    ) -> AutoSimulationResult:
        environment = self.environment_builder.build()
        fidelity = score_twin_fidelity(twin_mode, environment, unsupported)
        return AutoSimulationResult(
            status=UNSUPPORTED_PROTOCOL_TWIN,
            protocol=protocol,
            protocol_twin_mode=twin_mode,
            runtime=runtime,
            environment_twin=environment,
            twin_fidelity=fidelity,
            scorecard=None,
            recon_report=None,
            selected_drills=[],
            executable_drills_ran=False,
            regression_case_count=0,
            modes_tested=[],
            unsupported_components=fidelity.unsupported_components,
            resolution=resolution,
        )


def run_zero_blue_score():
    from eval.scoring import BlueScore

    return BlueScore(
        true_positives=0,
        false_positives=0,
        false_negatives=0,
        true_negatives=0,
        action_correctness=0.0,
        ordering_robustness=0.0,
        impact_reduction=0.0,
        no_label_robustness=1.0,
        private_orderflow_handling=0.0,
        overall=0.0,
    )


def run_auto_simulation_sync(request: AutoSimulationRequest) -> AutoSimulationResult:
    return asyncio.run(AutoSimulationRunner().run(request))
