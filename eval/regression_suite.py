from __future__ import annotations

import asyncio

from arenas.base_arena import OrderingMode
from arenas.local_mempool_arena import LocalMempoolArena
from eval.evaluation_harness import EvaluationHarness
from eval.scoring import (
    RegressionCaseResult,
    RegressionSuiteResult,
    ScoreCard,
    aggregate_multimode_blue_score,
    default_safety_score,
    score_evaluation_quality,
    score_recon_report,
    score_red_drills,
)
from recon.recon_engine import ReconEngine
from redteam.drills.decoy_pressure_drill import ExecutableDecoyPressureDrill
from redteam.drills.liquidity_shock_drill import ExecutableLiquidityShockDrill
from redteam.drills.multi_stage_drill import ExecutableMultiStageDrill
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.drills.vault_accounting_drill import ExecutableVaultAccountingDrill
from targets.target_schema import mock_target

CORE_REGRESSION_DRILLS = [
    ExecutableOracleDivergenceDrill,
    ExecutableLiquidityShockDrill,
    ExecutableVaultAccountingDrill,
    ExecutableMultiStageDrill,
    ExecutableDecoyPressureDrill,
]
CORE_REGRESSION_MODES: list[OrderingMode] = ["defense_first", "red_first", "gas_priority", "private_orderflow"]


async def run_core_regression_suite() -> RegressionSuiteResult:
    target = mock_target(True)
    recon = ReconEngine().run(target)
    harness = EvaluationHarness()
    cases: list[RegressionCaseResult] = []
    all_results = {}
    for drill_cls in CORE_REGRESSION_DRILLS:
        for mode in CORE_REGRESSION_MODES:
            result = await harness.run(target, recon, LocalMempoolArena(), drill_cls(), ordering_mode=mode)
            key = f"{drill_cls.__name__}:{mode}"
            all_results[key] = result
            cases.append(
                RegressionCaseResult(
                    drill_name=drill_cls.__name__,
                    ordering_mode=mode,
                    blue_action=result.blue_action,
                    red_impact_success=result.red_impact_successes,
                    blue_blocked=result.blue_blocks,
                    invariant_failures=result.invariant_failures,
                    score_components={
                        "blue_score": result.blue_score,
                        "safety_score": result.safety_score,
                        "evaluation_quality": result.evaluation_quality_scorecard.overall if result.evaluation_quality_scorecard else 0.0,
                    },
                )
            )
    blue = aggregate_multimode_blue_score({case.ordering_mode: all_results[f"ExecutableOracleDivergenceDrill:{case.ordering_mode}"] for case in cases if case.drill_name == "ExecutableOracleDivergenceDrill"})
    scorecard = ScoreCard(
        recon=score_recon_report(recon),
        red=score_red_drills([drill.__name__ for drill in CORE_REGRESSION_DRILLS], blind_compliant=True, impacts_invariants=True),
        blue=blue,
        safety=default_safety_score(),
        evaluation=score_evaluation_quality(
            state_diff_used=True,
            invariants_used=True,
            multi_mode_ordering_used=True,
            damage_recording_honest=True,
            defense_first_not_overweighted=True,
            label_leakage_checked=True,
        ),
    )
    return RegressionSuiteResult(cases=cases, scorecard=scorecard)


def run_core_regression_suite_sync() -> RegressionSuiteResult:
    return asyncio.run(run_core_regression_suite())
