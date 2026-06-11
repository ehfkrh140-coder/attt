from __future__ import annotations

from core.capability_boundary import (
    FORBIDDEN_OUTSIDE_MODELED_INSIDE_MATRIX,
    ForbiddenOutsideModeledInsideMapping,
    PermanentForbiddenCapability,
    matrix_by_forbidden,
    validate_matrix_complete,
)

ForbiddenOutsideModeledInsideMatrix = FORBIDDEN_OUTSIDE_MODELED_INSIDE_MATRIX


def get_modeled_inside_equivalent(capability: PermanentForbiddenCapability) -> ForbiddenOutsideModeledInsideMapping:
    return matrix_by_forbidden()[capability]


def matrix_is_complete() -> bool:
    return validate_matrix_complete()
