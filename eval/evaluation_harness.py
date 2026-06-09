from __future__ import annotations

from arenas.base_arena import OrderingMode, SUPPORTED_ORDERING_MODES
from blue.defender_engine import DefenderEngine
from eval.invariant_checker import check_all
from eval.label_leakage_checker import has_label_leakage
from eval.scoring import EvaluationResult, MultiModeEvaluationResult
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
        blue_action = DefenderEngine().defend(arena, observables)
        receipts = arena.mine_pending(ordering_mode=ordering_mode, seed=seed)
        post = arena.get_state()
        impact = await drill.assert_impact(arena, trace)
        failures = check_all(recon_report.invariants, post)
        state_diff = diff_states(pre, post)
        damage_recorded = self._damage_recorded(pre, post, failures)
        blocked = 1 if impact.blocked_by_blue else 0
        red_impact = 1 if (impact.impact_success or (damage_recorded and not impact.blocked_by_blue)) else 0
        action_correct = 1.0 if blue_action.action_type == "pause_price_sensitive_actions" else 0.0
        blue_score = self._score_single_mode(ordering_mode, blocked, red_impact, action_correct, has_label_leakage(observables))
        return EvaluationResult(
            run_id=f"mock-run-{ordering_mode}",
            target_protocol=target.protocol_name,
            fork_block=target.fork_block,
            recon_score=1.0 if recon_report.risk_hypotheses else 0.0,
            red_score=1.0 if trace.tx_intents else 0.0,
            blue_score=blue_score,
            safety_score=1.0,
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
        )

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
            return weight if (blocked or red_impact) else 0.0
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
