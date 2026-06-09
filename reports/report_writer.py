from __future__ import annotations

from core.safety import SafetyGuard
from eval.scoring import ScoreCard


def write_safe_report(result) -> str:
    report = f"Evaluation {result.run_id}: blue_blocks={result.blue_blocks}, labels=safe-only local-only arena-contained"
    SafetyGuard().assert_safe_report(report)
    return report


def write_beginner_summary(scorecard: ScoreCard) -> str:
    report = f"""DeFi Defense Simulation Summary
- Recon score: {scorecard.recon.overall:.2f}
- Red drill score: {scorecard.red.overall:.2f}
- Blue defense score: {scorecard.blue.overall:.2f}
- Safety score: {scorecard.safety.overall:.2f}
- Evaluation quality score: {scorecard.evaluation.overall:.2f}

Plain English:
- Safety boundary is strong when safety score is near 1.00.
- Red drills are diverse enough for the mock MVP when red score is high.
- Blue handles visible attacks better than hidden private-orderflow cases when blue score is lower than evaluation quality.
- Recon is target-specific but still manifest-driven in this MVP.
- EVM/Sui real adapters are not implemented yet.
"""
    SafetyGuard().assert_safe_report(report)
    return report
