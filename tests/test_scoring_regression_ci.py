from __future__ import annotations

import asyncio
from pathlib import Path

from arenas.local_mempool_arena import LocalMempoolArena
from eval.evaluation_harness import EvaluationHarness
from eval.regression_suite import CORE_REGRESSION_DRILLS, CORE_REGRESSION_MODES, run_core_regression_suite_sync
from eval.scoring import (
    score_blue_outcome,
    score_recon_report,
    score_red_drills,
    score_safety_checks,
)
from recon.recon_engine import ReconEngine
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from reports.report_writer import write_beginner_summary
from targets.target_schema import mock_target


def run(coro):
    return asyncio.run(coro)


def test_scoring_separates_blue_from_evaluation_quality():
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill(), ordering_mode="red_first")

    result = run(scenario())
    assert result.red_impact_successes == 1
    assert result.blue_blocks == 0
    assert result.blue_score == 0.0
    assert result.evaluation_quality_scorecard is not None
    assert result.evaluation_quality_scorecard.damage_recording_honest == 1.0


def test_scoring_penalizes_false_positive_on_decoy():
    clean = score_blue_outcome(true_negatives=1, action_correctness=1.0, ordering_robustness=1.0, impact_reduction=1.0, no_label_robustness=1.0)
    false_positive = score_blue_outcome(false_positives=1, action_correctness=0.0, ordering_robustness=0.0, impact_reduction=1.0, no_label_robustness=1.0)
    assert false_positive.overall < clean.overall


def test_scoring_penalizes_private_orderflow_miss():
    handled = score_blue_outcome(true_positives=1, private_orderflow_handling=1.0, ordering_robustness=1.0, impact_reduction=1.0, no_label_robustness=1.0)
    missed = score_blue_outcome(false_negatives=1, private_orderflow_handling=0.0, ordering_robustness=0.0, impact_reduction=0.0, no_label_robustness=1.0)
    assert missed.overall < handled.overall


def test_scoring_rewards_multimode_robustness():
    weak = score_blue_outcome(true_positives=1, false_negatives=3, ordering_robustness=0.25, impact_reduction=0.25, no_label_robustness=1.0)
    robust = score_blue_outcome(true_positives=4, ordering_robustness=1.0, impact_reduction=1.0, no_label_robustness=1.0)
    assert robust.overall > weak.overall


def test_red_score_requires_independent_drill_diversity():
    one = score_red_drills(["ExecutableOracleDivergenceDrill"])
    diverse = score_red_drills([drill.__name__ for drill in CORE_REGRESSION_DRILLS])
    assert diverse.overall > one.overall
    assert diverse.independent_drill_count > one.independent_drill_count


def test_recon_score_uses_dependency_and_invariant_coverage():
    rich = score_recon_report(ReconEngine().run(mock_target(True)))
    sparse_recon = ReconEngine().run(type(mock_target(True))(
        protocol_name="SparseVault",
        runtime="mock",
        network_name="local-mock",
        fork_block=None,
        target_mode="manifest",
        in_scope_contracts=[{"name": "SparseVault", "address": "local://sparse-vault", "category": "vault"}],
        authorized_scope=True,
        scope_confirmed=True,
    ))
    sparse = score_recon_report(sparse_recon)
    assert rich.dependency_graph_completeness > sparse.dependency_graph_completeness
    assert rich.invariant_usefulness > sparse.invariant_usefulness


def test_safety_score_blocks_public_rpc_value_and_scope():
    strong = score_safety_checks(
        public_rpc_blocked=True,
        public_chain_blocked=True,
        value_transfer_blocked=True,
        out_of_scope_blocked=True,
        raw_provider_access_blocked=True,
        report_sanitization_passed=True,
        adapter_gating_enforced=True,
    )
    weak = score_safety_checks(
        public_rpc_blocked=False,
        public_chain_blocked=True,
        value_transfer_blocked=False,
        out_of_scope_blocked=False,
        raw_provider_access_blocked=True,
        report_sanitization_passed=True,
        adapter_gating_enforced=True,
    )
    assert weak.overall < strong.overall


def test_regression_suite_runs_core_drills_across_modes():
    result = run_core_regression_suite_sync()
    expected = len(CORE_REGRESSION_DRILLS) * len(CORE_REGRESSION_MODES)
    assert len(result.cases) == expected
    assert result.scorecard.recon.overall > 0
    assert result.scorecard.evaluation.multi_mode_ordering_used == 1.0
    assert {case.ordering_mode for case in result.cases} == set(CORE_REGRESSION_MODES)


def test_beginner_summary_report_contains_no_unsafe_artifacts():
    result = run_core_regression_suite_sync()
    report = write_beginner_summary(result.scorecard)
    assert "DeFi Defense Simulation Summary" in report
    assert "Safety boundary" in report
    forbidden = ["raw_calldata", "private_key", "mnemonic", "http://", "https://", "send_raw_transaction"]
    assert not any(token in report.lower() for token in forbidden)


def test_github_actions_workflow_exists():
    workflow = Path(".github/workflows/test.yml")
    assert workflow.exists()
    text = workflow.read_text()
    assert "pytest -q" in text
    assert "python main.py" in text
    lowered = text.lower()
    forbidden = ["secrets", "private_key", "infura", "alchemy", "quicknode", "ankr", "blastapi", "publicnode", "mainnet"]
    assert not any(token in lowered for token in forbidden)
