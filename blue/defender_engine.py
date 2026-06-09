from __future__ import annotations

from arenas.base_arena import OrderingMode
from blue.action_planner import DefenseAction, plan_action
from blue.context import DefenderContext
from blue.defense_executor import execute_defense
from blue.threat_classifier import classify
from blue.tx_feature_decoder import decode_safe_features
from redteam.executable_drill import BlindObservableBundle


class DefenderEngine:
    def defend(
        self,
        arena,
        observables: BlindObservableBundle,
        recon_report=None,
        ordering_mode: OrderingMode = "defense_first",
    ) -> DefenseAction:
        observables.assert_no_ground_truth()
        features = decode_safe_features(observables.pending_features)
        state = arena.get_state()
        visibility_mode = str(observables.state_window.get("visibility_mode", getattr(arena, "private_orderflow", False) and "private_orderflow" or "public_local_mempool"))
        context = DefenderContext.from_inputs(
            recon_report=recon_report,
            ordering_mode=ordering_mode,
            visibility_mode=visibility_mode,
            current_state=state,
            recent_state_window=observables.state_window,
            pending_feature_count=len(features),
        )
        finding = classify(features, state, context)
        action = plan_action(finding)
        execute_defense(arena, action)
        return action
