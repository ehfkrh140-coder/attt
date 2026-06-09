from __future__ import annotations

from core.errors import ValidationError
from redteam.executable_drill import ExecutableDrill, StaticRedScenario

ERROR_REQUIRES_EXECUTABLE_DRILL = "RED_CHALLENGE_REQUIRES_EXECUTABLE_DRILL"


def validate_red_challenge(challenge: object) -> ExecutableDrill:
    if isinstance(challenge, StaticRedScenario):
        raise ValidationError(ERROR_REQUIRES_EXECUTABLE_DRILL)
    required = ["precheck", "prepare", "arm", "trigger", "collect_blue_observables", "assert_impact"]
    if not all(callable(getattr(challenge, name, None)) for name in required):
        raise ValidationError(ERROR_REQUIRES_EXECUTABLE_DRILL)
    return challenge  # type: ignore[return-value]
