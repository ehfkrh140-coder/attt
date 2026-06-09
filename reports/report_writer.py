from __future__ import annotations

from core.safety import SafetyGuard


def write_safe_report(result) -> str:
    report = f"Evaluation {result.run_id}: blue_blocks={result.blue_blocks}, labels=safe-only local-only arena-contained"
    SafetyGuard().assert_safe_report(report)
    return report
