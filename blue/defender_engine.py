from __future__ import annotations

from blue.action_planner import DefenseAction, plan_action
from blue.defense_executor import execute_defense
from blue.threat_classifier import classify
from blue.tx_feature_decoder import decode_safe_features
from redteam.executable_drill import BlindObservableBundle


class DefenderEngine:
    def defend(self, arena, observables: BlindObservableBundle) -> DefenseAction:
        observables.assert_no_ground_truth()
        features = decode_safe_features(observables.pending_features)
        finding = classify(features, arena.get_state())
        action = plan_action(finding)
        execute_defense(arena, action)
        return action
