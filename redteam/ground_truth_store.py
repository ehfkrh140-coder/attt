"""Evaluation-only storage for hidden Red ground truth.

Blue modules must never import this module. The architectural test scans blue/ for this import.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GroundTruthRecord:
    drill_id: str
    expected_action: str
    hidden_intent: str
