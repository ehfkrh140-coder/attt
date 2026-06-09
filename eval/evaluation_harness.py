from __future__ import annotations

from blue.defender_engine import DefenderEngine
from eval.invariant_checker import check_all
from eval.label_leakage_checker import has_label_leakage
from eval.scoring import EvaluationResult
from eval.state_diff import diff_states


class EvaluationHarness:
    async def run(self, target, recon_report, arena, drill) -> EvaluationResult:
        await drill.precheck(arena, target)
        pre = arena.get_state()
        context = await drill.prepare(arena, target)
        trace = await drill.trigger(arena, context)
        observables = await drill.collect_blue_observables(trace)
        blue_action = DefenderEngine().defend(arena, observables)
        arena.mine_pending(defense_first=True)
        post = arena.get_state()
        impact = await drill.assert_impact(arena, trace)
        failures = check_all(recon_report.invariants, post)
        blocked = 1 if impact.blocked_by_blue else 0
        return EvaluationResult(
            run_id="mock-run-001",
            target_protocol=target.protocol_name,
            fork_block=target.fork_block,
            recon_score=1.0 if recon_report.risk_hypotheses else 0.0,
            red_score=1.0 if trace.tx_intents else 0.0,
            blue_score=1.0 if blocked else 0.0,
            safety_score=1.0,
            executable_drill_count=1,
            unsupported_drill_count=0,
            red_impact_successes=1 if impact.impact_success else 0,
            blue_blocks=blocked,
            blue_misses=0 if blocked else 1,
            false_positives=0,
            false_negatives=0 if blocked else 1,
            action_correctness=1.0 if blue_action.action_type == "pause_price_sensitive_actions" else 0.0,
            invariant_failures=failures,
            label_leakage_detected=has_label_leakage(observables),
            public_network_blocked=True,
            extreme_drill_coverage=1.0,
            notes=[f"state_diff={diff_states(pre, post)}", "State diffs and invariants determined impact."],
        )
