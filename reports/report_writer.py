from __future__ import annotations

from typing import Any

from core.safety import SafetyGuard
from eval.scoring import ScoreCard


def write_safe_report(result) -> str:
    report = f"Evaluation {result.run_id}: blue_blocks={result.blue_blocks}, labels=safe-only local-only arena-contained"
    SafetyGuard().assert_safe_report(report)
    return report


def write_beginner_summary(
    scorecard: ScoreCard,
    *,
    regression_case_count: int | None = None,
    modes_tested: list[str] | tuple[str, ...] | None = None,
    protocol_twin_mode: str = "mockarena",
    environment_coverage: str = "orderflow, keeper, oracle, liquidity, bridge, offchain, user intent, network",
    twin_fidelity_score: float | None = None,
    unsupported_components: list[str] | tuple[str, ...] | None = None,
    executable_drills_ran: bool = True,
    result_mode: str = "MockArena-only",
) -> str:
    case_line = f"- Regression cases: {regression_case_count}\n" if regression_case_count is not None else ""
    modes_line = f"- Modes tested: {', '.join(modes_tested)}\n" if modes_tested else ""
    fidelity_line = f"- Twin Fidelity Score: {twin_fidelity_score:.2f}\n" if twin_fidelity_score is not None else ""
    unsupported = ", ".join(unsupported_components or []) if unsupported_components else "none"
    report = f"""DeFi Defense Simulation Summary
- Recon score: {scorecard.recon.overall:.2f}
- Red drill score: {scorecard.red.overall:.2f}
- Blue defense score: {scorecard.blue.overall:.2f}
- Safety score: {scorecard.safety.overall:.2f}
- Evaluation quality score: {scorecard.evaluation.overall:.2f}
{case_line}{modes_line}- Protocol Twin mode: {protocol_twin_mode}
- Environment Twin coverage: {environment_coverage}
{fidelity_line}- Unsupported components: {unsupported}
- Executable drills ran: {'yes' if executable_drills_ran else 'no'}
- Result mode: {result_mode}

Plain English:
- Safety boundary is strong when safety score is near 1.00.
- Red drills are diverse enough for the mock MVP when red score is high.
- Blue handles visible local drills better than hidden private-orderflow cases when blue score is lower than evaluation quality.
- Recon is target-specific but still manifest-driven in this MVP.
- MockArena only: executable drill support is currently limited to the contained mock runtime unless an adapter is explicitly ready.
- EVM/Sui adapters are gated and not implemented yet.
"""
    SafetyGuard().assert_safe_report(report)
    return report


def write_protocol_twin_summary(result: Any) -> str:
    scorecard = result.scorecard
    if scorecard is None:
        report = "\n".join(
            [
                "Protocol Twin Simulation Summary",
                f"- Protocol: {result.protocol}",
                f"- Protocol Twin mode: {result.protocol_twin_mode}",
                f"- Result mode: {result.status}",
                f"- Twin Fidelity Score: {result.twin_fidelity.overall:.2f}",
                "- Environment Twin coverage: local external-world emulation configured",
                f"- Unsupported components: {', '.join(result.unsupported_components) if result.unsupported_components else 'none'}",
                f"- Local fork reachable: {'no' if result.status == 'LOCAL_FORK_UNAVAILABLE' else 'unknown'}",
                f"- Read-only discovery: {getattr(result, 'read_only_discovery', 'no')}",
                f"- Executable drills ran: {'yes' if result.executable_drills_ran else 'no'}",
                f"- Execution gated: {'no' if result.executable_drills_ran else 'yes'}",
                "- MockArena fallback: no" if result.protocol == "aave_v3" else "- Red drills are selected automatically when executable simulation is supported.",
            ]
        )
    else:
        report = write_beginner_summary(
            scorecard,
            regression_case_count=result.regression_case_count,
            modes_tested=result.modes_tested,
            protocol_twin_mode=result.protocol_twin_mode,
            twin_fidelity_score=result.twin_fidelity.overall,
            unsupported_components=result.unsupported_components,
            executable_drills_ran=result.executable_drills_ran,
            result_mode=result.status,
        )
        extra_lines: list[str] = []
        if getattr(result, "read_only_discovery", "no") != "no":
            extra_lines.extend(
                [
                    f"- Read-only discovery: {result.read_only_discovery}",
                    "- Execution gated: yes",
                    f"- Discovered contracts: {', '.join(result.discovered_contracts) if result.discovered_contracts else 'partial'}",
                    f"- Selected drill recommendations: {', '.join(result.selected_drills) if result.selected_drills else 'none'}",
                ]
            )
        if extra_lines:
            report = report.rstrip() + "\n" + "\n".join(extra_lines) + "\n"
            SafetyGuard().assert_safe_report(report)
        return report
    SafetyGuard().assert_safe_report(report)
    return report
