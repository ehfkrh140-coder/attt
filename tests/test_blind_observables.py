from __future__ import annotations

import asyncio

import pytest

from arenas.local_mempool_arena import LocalMempoolArena
from blue.defender_engine import DefenderEngine
from blue.threat_classifier import classify
from blue.tx_feature_decoder import decode_safe_features
from eval.evaluation_harness import EvaluationHarness
from recon.recon_engine import ReconEngine
from redteam.drills.decoy_pressure_drill import ExecutableDecoyPressureDrill
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from redteam.executable_drill import ANSWER_LIKE_LABELS, BlindObservableBundle, BlindTxFeature
from targets.target_schema import mock_target


def collect_oracle_bundle():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableOracleDivergenceDrill()
        context = await drill.prepare(arena, mock_target(True))
        trace = await drill.trigger(arena, context)
        return await drill.collect_blue_observables(trace)

    return asyncio.run(scenario())


def test_blue_does_not_receive_exact_function_category():
    bundle = collect_oracle_bundle()
    for feature in bundle.pending_features:
        feature_dict = feature.to_dict()
        assert "function_category" not in feature_dict
        assert "calldata_label" not in feature_dict


def test_blue_cannot_access_red_intent_labels():
    bundle = collect_oracle_bundle()
    observable_text = str({
        "pending_features": [feature.to_dict() for feature in bundle.pending_features],
        "state_window": bundle.state_window,
    }).lower()
    forbidden = ANSWER_LIKE_LABELS | {"benign_decoy"}
    assert not any(label in observable_text for label in forbidden)


def test_blue_still_blocks_oracle_drill_using_blind_features():
    async def scenario():
        target = mock_target(True)
        recon = ReconEngine().run(target)
        return await EvaluationHarness().run(target, recon, LocalMempoolArena(), ExecutableOracleDivergenceDrill())

    result = asyncio.run(scenario())
    assert result.blue_blocks == 1
    assert result.red_impact_successes == 0
    assert result.action_correctness == 1.0


def test_blue_fails_if_policy_depends_on_function_category():
    decoded = decode_safe_features([{"function_category": "oracle_divergence"}])
    assert all("function_category" not in feature for feature in decoded)
    finding = classify(decoded, {})
    assert finding.confidence < 0.8
    assert finding.risk_type != "local_invariant_pressure"


def test_decoy_blind_features_do_not_trigger_pause():
    async def scenario():
        arena = LocalMempoolArena()
        drill = ExecutableDecoyPressureDrill()
        context = await drill.prepare(arena, mock_target(True))
        trace = await drill.trigger(arena, context)
        bundle = await drill.collect_blue_observables(trace)
        action = DefenderEngine().defend(arena, bundle)
        return action, bundle

    action, bundle = asyncio.run(scenario())
    assert action.action_type == "monitor"
    assert all(feature.call_shape == "routine_local_activity" for feature in bundle.pending_features)


def test_blind_observable_bundle_rejects_answer_like_labels():
    bundle = BlindObservableBundle(
        drill_id="blind-test",
        pending_features=[
            BlindTxFeature(
                target_category="price_reference_module",
                call_shape="local_state_change",
                sender_profile="new_research_account",
                gas_profile="local_priority",
                value_bucket="zero",
                timing_pattern="clustered_pending",
                dependency_context=["oracle_path"],
                state_delta_hint="oracle_divergence",
                visibility_mode="public_local_mempool",
                local_ordering_hint="priority_cluster",
            )
        ],
        state_window={"pending_count": 1},
    )
    with pytest.raises(AssertionError, match="answer-like"):
        bundle.assert_no_ground_truth()
