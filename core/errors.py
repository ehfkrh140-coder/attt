class LabError(Exception):
    """Base error for the lab."""


class SafetyGuardError(LabError):
    """Raised when a drill or defense action attempts to escape containment."""


class ValidationError(LabError):
    """Raised when a lab object is structurally invalid."""
