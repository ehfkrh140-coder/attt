from __future__ import annotations

from redteam.executable_drill import ANSWER_LIKE_LABELS


def has_label_leakage(payload: object) -> bool:
    lowered = str(payload).lower()
    return any(token in lowered for token in ANSWER_LIKE_LABELS)
