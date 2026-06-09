from __future__ import annotations


def has_label_leakage(payload: object) -> bool:
    lowered = str(payload).lower()
    return any(token in lowered for token in ["expected_action", "hidden_ground_truth", "answer_key", "malicious"])
