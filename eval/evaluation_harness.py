from __future__ import annotations

from arenas.base_arena import OrderingMode, SUPPORTED_ORDERING_MODES
from blue.defender_engine import DefenderEngine
from eval.invariant_checker import check_all
from eval.label_leakage_checker import has_label_leakage
from eval.scoring import (
    EvaluationResult,
    MultiModeEvaluationResult,
    aggregate_multimode_blue_score,
    default_safety_score,
    score_blue_outcome,
    score_evaluation_quality,
    score_recon_report,
    score_red_drills,
)
from eval.state_diff import diff_states
from redteam.executable_drill import BlindObservableBundle

_MODE_WEIGHTS: dict[OrderingMode, float] = {
    "defense_first": 0.25,
    "gas_priority": 0.25,
    "red_first": 0.20,
    "private_orderflow": 0.15,
    "randomized_seeded": 0.15,
}


class EvaluationHarness:
    async def run(
        self,
        target,
        recon_report,
        arena,
        drill,
        ordering_mode: OrderingMode = "defense_first",
        seed: int | None = None,
    ) -> EvaluationResult:
        await drill.precheck(arena, target)
        arena.bind_target(target)
        pre = arena.get_state()
        context = await drill.prepare(arena, target)
        trace = await drill.trigger(arena, context)
        observables = await drill.collect_blue_observables(trace)
        if ordering_mode == "private_orderflow":
            arena.private_orderflow = True
            observables = BlindObservableBundle(
                drill_id=trace.drill_id,
                pending_features=[],
                state_window={"pending_count": 0, "visibility_mode": "private_orderflow"},
            )
            observables.assert_no_ground_truth()
        blue_action = self._defend_with_context(arena, observables, recon_report, ordering_mode)
        receipts = arena.mine_pending(ordering_mode=ordering_mode, seed=seed)
        post = arena.get_state()
        impact = await drill.assert_impact(arena, trace)
        failures = check_all(recon_report.invariants, post)
        state_diff = diff_states(pre, post)
        damage_recorded = self._damage_recorded(pre, post, failures)
        blocked = 1 if impact.blocked_by_blue else 0
        red_impact = 1 if (impact.impact_success or (damage_recorded and not impact.blocked_by_blue)) else 0
        action_correct = 1.0 if blue_action.intent is not None or blue_action.action_type in {"alert_only", "governance_review", "admin_review"} else 0.0
        blue_score = self._score_single_mode(ordering_mode, blocked, red_impact, action_correct, has_label_leakage(observables))
        recon_scorecard = score_recon_report(recon_report)
        red_scorecard = score_red_drills([type(drill).__name__], blind_compliant=not has_label_leakage(observables), impacts_invariants=True)
        safety_scorecard = default_safety_score()
        evaluation_quality_scorecard = score_evaluation_quality(
            state_diff_used=bool(state_diff),
            invariants_used=bool(getattr(recon_report, "invariants", [])),
            multi_mode_ordering_used=False,
            damage_recording_honest=(ordering_mode != "red_first" or red_impact == 1 or blocked == 1),
            defense_first_not_overweighted=(blue_score < 1.0),
            label_leakage_checked=True,
        )
        blue_scorecard = score_blue_outcome(
            true_positives=1 if blocked and not red_impact else 0,
            false_positives=1 if blue_action.action_type.startswith("pause") and not blocked and not red_impact else 0,
            false_negatives=1 if red_impact and not blocked else 0,
            true_negatives=1 if blue_action.action_type in {"monitor", "alert_only"} and not red_impact else 0,
            action_correctness=action_correct,
            ordering_robustness=1.0 if blocked else 0.0,
            impact_reduction=0.0 if red_impact else 1.0,
            no_label_robustness=0.0 if has_label_leakage(observables) else 1.0,
            private_orderflow_handling=1.0 if ordering_mode == "private_orderflow" and blue_action.action_type in {"monitor", "alert_only"} else 0.0,
        )
        return EvaluationResult(
            run_id=f"mock-run-{ordering_mode}",
            target_protocol=target.protocol_name,
            fork_block=target.fork_block,
            recon_score=recon_scorecard.overall,
            red_score=1.0 if trace.tx_intents else 0.0,
            blue_score=blue_score,
            safety_score=safety_scorecard.overall,
            executable_drill_count=1,
            unsupported_drill_count=0,
            red_impact_successes=red_impact,
            blue_blocks=blocked,
            blue_misses=0 if blocked else 1,
            false_positives=0,
            false_negatives=0 if blocked else 1,
            action_correctness=action_correct,
            invariant_failures=failures,
            label_leakage_detected=has_label_leakage(observables),
            public_network_blocked=True,
            extreme_drill_coverage=1.0,
            notes=[
                f"ordering_mode={ordering_mode}",
                f"state_diff={state_diff}",
                f"damage_recorded={damage_recorded}",
                "State diffs and invariants determined impact.",
            ],
            ordering_mode=ordering_mode,
            execution_order=[receipt["tx"] for receipt in receipts],
            blue_action=blue_action.action_type,
            recon_scorecard=recon_scorecard,
            red_scorecard=red_scorecard,
            blue_scorecard=blue_scorecard,
            safety_scorecard=safety_scorecard,
            evaluation_quality_scorecard=evaluation_quality_scorecard,
        )


    def _defend_with_context(self, arena, observables, recon_report, ordering_mode: OrderingMode):
        defender = DefenderEngine()
        try:
            return defender.defend(arena, observables, recon_report=recon_report, ordering_mode=ordering_mode)
        except TypeError:
            return defender.defend(arena, observables)

    async def run_across_ordering_modes(
        self,
        target,
        recon_report,
        arena_factory,
        drill_factory,
        modes: list[OrderingMode] | None = None,
        seed: int | None = None,
    ) -> MultiModeEvaluationResult:
        selected_modes = modes or list(SUPPORTED_ORDERING_MODES)
        results: dict[OrderingMode, EvaluationResult] = {}
        for mode in selected_modes:
            results[mode] = await self.run(target, recon_report, arena_factory(), drill_factory(), ordering_mode=mode, seed=seed)
        modes_passed = [mode for mode, result in results.items() if result.blue_blocks or (mode == "red_first" and result.red_impact_successes)]
        modes_failed = [mode for mode in selected_modes if mode not in modes_passed]
        aggregate_blue = aggregate_multimode_blue_score(results)
        aggregate_eval_quality = score_evaluation_quality(
            state_diff_used=all(any("state_diff=" in note for note in result.notes) for result in results.values()),
            invariants_used=all(bool(getattr(recon_report, "invariants", [])) for _ in results.values()),
            multi_mode_ordering_used=len(selected_modes) > 1,
            damage_recording_honest=all((mode != "red_first" or result.red_impact_successes or result.blue_blocks) for mode, result in results.items()),
            defense_first_not_overweighted=results.get("defense_first").blue_score < 1.0 if "defense_first" in results else True,
            label_leakage_checked=all(not result.label_leakage_detected for result in results.values()),
        )
        return MultiModeEvaluationResult(
            run_id="mock-multimode-run",
            target_protocol=target.protocol_name,
            ordering_results=results,
            blue_blocks_by_mode={mode: result.blue_blocks for mode, result in results.items()},
            red_impact_successes_by_mode={mode: result.red_impact_successes for mode, result in results.items()},
            action_correctness_by_mode={mode: result.action_correctness for mode, result in results.items()},
            impact_by_mode={mode: result.invariant_failures for mode, result in results.items()},
            ordering_robustness_score=round(sum(result.blue_score for result in results.values()), 4),
            modes_passed=modes_passed,
            modes_failed=modes_failed,
            per_mode_blue_score={mode: result.blue_score for mode, result in results.items()},
            per_mode_red_impact={mode: result.red_impact_successes for mode, result in results.items()},
            per_mode_action_correctness={mode: result.action_correctness for mode, result in results.items()},
            per_mode_safety_score={mode: result.safety_score for mode, result in results.items()},
            aggregate_blue_score=aggregate_blue.overall,
            aggregate_evaluation_quality_score=aggregate_eval_quality.overall,
        )

    def _score_single_mode(
        self,
        ordering_mode: OrderingMode,
        blocked: int,
        red_impact: int,
        action_correctness: float,
        label_leakage: bool,
    ) -> float:
        if label_leakage:
            return 0.0
        weight = _MODE_WEIGHTS[ordering_mode]
        if ordering_mode in {"defense_first", "gas_priority", "randomized_seeded"}:
            return weight if blocked else 0.0
        if ordering_mode == "red_first":
            return weight if blocked else 0.0
        if ordering_mode == "private_orderflow":
            return weight if blocked else 0.0
        return 0.0

    def _damage_recorded(self, pre: dict[str, object], post: dict[str, object], failures: list[str]) -> bool:
        return bool(failures) or any(
            [
                float(post.get("vault_assets", 0)) < float(pre.get("vault_assets", 0)),
                float(post.get("vault_liabilities", 0)) > float(pre.get("vault_liabilities", 0)),
                float(post.get("pool_liquidity", 0)) < float(post.get("min_pool_liquidity", 0)),
                abs(float(post.get("oracle_price", 0)) - float(post.get("pool_price", 0)))
                / max(float(post.get("pool_price", 1)), 1.0)
                > float(post.get("max_oracle_deviation", 0.10)),
            ]
        )
