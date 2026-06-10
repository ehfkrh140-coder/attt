from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tomllib

from core.safety import SafetyGuard
from eval.regression_suite import run_core_regression_suite_sync
from reports.report_writer import write_protocol_twin_summary
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from targets.protocol_catalog import MISSING_PROTOCOL_ROOT_ADDRESS, UNSUPPORTED_PROTOCOL_TWIN

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
UNSAFE_TOKENS = [
    "raw_calldata",
    "calldata:",
    "private_key",
    "mnemonic",
    "seed phrase",
    "send_raw_transaction",
    "sign_transaction",
    "account.sign_transaction",
    "infura",
    "alchemy",
    "quicknode",
    "ankr",
    "blastapi",
    "publicnode",
]


def _check(name: str, condition: bool, results: list[tuple[str, bool]]) -> None:
    results.append((name, bool(condition)))


def _safe(text: str) -> bool:
    SafetyGuard().assert_safe_report(text)
    lowered = text.lower()
    return not any(token in lowered for token in UNSAFE_TOKENS)


def main() -> int:
    results: list[tuple[str, bool]] = []

    # Import checks for core release modules.
    import blue.defender_engine  # noqa: F401
    import eval.evaluation_harness  # noqa: F401
    import recon.recon_engine  # noqa: F401
    import redteam.drill_planner  # noqa: F401

    version_text = (ROOT / "VERSION").read_text().strip() if (ROOT / "VERSION").exists() else ""
    pyproject_version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    _check("Version", version_text == VERSION and pyproject_version == VERSION, results)

    regression = run_core_regression_suite_sync()
    _check("Regression suite", len(regression.cases) >= 20 and regression.scorecard.safety.overall == 1.0, results)

    mock_result = run_auto_simulation_sync(AutoSimulationRequest(protocol="mock_lending"))
    main_summary = write_protocol_twin_summary(mock_result)
    _check("Main summary", "Twin Fidelity Score" in main_summary and _safe(main_summary), results)
    _check("Protocol Twin mock_lending", mock_result.executable_drills_ran and mock_result.protocol_twin_mode == "mockarena", results)

    aave_result = run_auto_simulation_sync(AutoSimulationRequest(protocol="aave_v3", network="ethereum"))
    aave_summary = write_protocol_twin_summary(aave_result)
    _check(
        "Aave V3 gated status",
        aave_result.status == MISSING_PROTOCOL_ROOT_ADDRESS and not aave_result.executable_drills_ran and _safe(aave_summary),
        results,
    )

    phase2a_result = run_auto_simulation_sync(
        AutoSimulationRequest(protocol="aave_v3", network="ethereum", root_address="aave-root", fork_block="latest")
    )
    phase2a_summary = write_protocol_twin_summary(phase2a_result)
    _check(
        "Phase 2A read-only smoke",
        phase2a_result.read_only_discovery == "yes"
        and not phase2a_result.executable_drills_ran
        and phase2a_result.protocol_twin_mode == "evm_fork_twin"
        and _safe(phase2a_summary),
        results,
    )

    haedal_result = run_auto_simulation_sync(AutoSimulationRequest(protocol="haedal"))
    haedal_summary = write_protocol_twin_summary(haedal_result)
    _check(
        "Haedal unsupported status",
        haedal_result.status == UNSUPPORTED_PROTOCOL_TWIN and not haedal_result.executable_drills_ran and _safe(haedal_summary),
        results,
    )

    docs = [
        ROOT / "README.md",
        ROOT / "docs" / "BEGINNER_RUNBOOK.md",
        ROOT / "docs" / "CAPABILITY_STATUS.md",
        ROOT / "docs" / "RELEASE_CHECKLIST.md",
    ]
    _check("Docs present", all(path.exists() for path in docs), results)
    _check("GitHub Actions workflow present", (ROOT / ".github" / "workflows" / "test.yml").exists(), results)

    capability = (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
    _check(
        "Gated adapter honesty",
        "EVM Fork Twin read-only/gated planning" in capability
        and "Sui State Twin" in capability
        and "real Haedal adapter" in capability,
        results,
    )
    _check("Safety report sanitizer", _safe(main_summary + "\n" + aave_summary + "\n" + phase2a_summary + "\n" + haedal_summary), results)

    overall = all(passed for _, passed in results)
    lines = ["MockArena MVP Verification"]
    for name, passed in results:
        lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    lines.append(f"- Overall: {'PASS' if overall else 'FAIL'}")
    output = "\n".join(lines)
    SafetyGuard().assert_safe_report(output)
    print(output)
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
