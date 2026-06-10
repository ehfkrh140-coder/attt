from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tomllib

from arenas.evm_fork_execution_arena import EvmForkExecutionArena, UNSUPPORTED_EXECUTABLE_FORK_DRILLS
from core.fork_execution_policy import ForkExecutionMode, default_fork_execution_mode
from core.safety import SafetyGuard
from redteam.local_tx_intent import LocalTxIntent
from eval.regression_suite import run_core_regression_suite_sync
from reports.report_writer import write_protocol_twin_summary
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync
from scripts.aave_readonly_discovery import run_discovery
from scripts.check_local_evm_fork import run_check
from scripts.phase2b_preflight import run_preflight
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
        AutoSimulationRequest(protocol="aave_v3", network="ethereum", root_address="aave-root", fork_block="latest", fixture_readonly=True)
    )
    phase2a_summary = write_protocol_twin_summary(phase2a_result)
    _check(
        "Phase 2A.1 read-only fixture smoke",
        phase2a_result.read_only_discovery == "fully_discovered"
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
        ROOT / "docs" / "PHASE_2A_DEPTH_AUDIT.md",
        ROOT / "docs" / "PHASE_2B_READINESS_CHECKLIST.md",
        ROOT / "docs" / "PHASE_2B_FORK_EXECUTION_DESIGN.md",
        ROOT / "docs" / "PHASE_2B_FIRST_DRILL_CANDIDATE.md",
        ROOT / "docs" / "PHASE_2B_PREFLIGHT.md",
        ROOT / "docs" / "templates" / "MANUAL_LIVE_FORK_SMOKE_RESULT_TEMPLATE.md",
    ]
    _check("Docs present", all(path.exists() for path in docs), results)
    _check("GitHub Actions workflow present", (ROOT / ".github" / "workflows" / "test.yml").exists(), results)

    phase2a2_scripts = [
        ROOT / "scripts" / "check_local_evm_fork.py",
        ROOT / "scripts" / "aave_readonly_discovery.py",
        ROOT / "scripts" / "manual_live_fork_smoke.py",
    ]
    _check("Phase 2A.2 smoke scripts present", all(path.exists() for path in phase2a2_scripts), results)
    script_text = "\n".join(path.read_text() for path in phase2a2_scripts if path.exists())
    _check(
        "Phase 2A.2 scripts stay read-only",
        "eth_sendTransaction" not in script_text
        and "eth_sendRawTransaction" not in script_text
        and "private_key" not in script_text
        and "mock_lending" not in script_text,
        results,
    )

    phase2b_preflight_tools = [
        ROOT / "scripts" / "record_live_fork_smoke_result.py",
        ROOT / "scripts" / "phase2b_preflight.py",
        ROOT / "docs" / "PHASE_2B_PREFLIGHT.md",
    ]
    _check("Phase 2B preflight tools present", all(path.exists() for path in phase2b_preflight_tools), results)
    preflight_text = "\n".join(path.read_text() for path in phase2b_preflight_tools if path.exists())
    _check(
        "Phase 2B preflight tools stay gated",
        "eth_sendTransaction" not in preflight_text
        and "eth_sendRawTransaction" not in preflight_text
        and "account.sign_transaction" not in preflight_text
        and "LOCAL_EXECUTION_ENABLED" not in preflight_text
        and "mock_lending" not in preflight_text,
        results,
    )
    phase2b_preflight_output = run_preflight(
        manual_smoke_result="docs/missing_manual_live_fork_smoke_result.md",
        target_manifest="targets/generated/missing_aave_v3_readonly.yaml",
        dependency_graph_review="docs/missing_dependency_graph_review.md",
    )
    _check(
        "Phase 2B preflight remains blocked",
        "Phase 2B readiness: FAIL" in phase2b_preflight_output
        and "Fork execution disabled: yes" in phase2b_preflight_output
        and "Execution arena unsupported: yes" in phase2b_preflight_output
        and _safe(phase2b_preflight_output),
        results,
    )

    phase2a2_check_output = run_check("http://127.0.0.1:1")
    phase2a2_aave_output = run_discovery(root_address="aave-root", fixture_readonly=True)
    depth_audit = (ROOT / "docs" / "PHASE_2A_DEPTH_AUDIT.md").read_text()
    phase2b_checklist = (ROOT / "docs" / "PHASE_2B_READINESS_CHECKLIST.md").read_text()
    _check(
        "Phase 2A QA audit docs",
        "Fixture-backed CI tests" in depth_audit
        and "Optional live local fork manual commands" in depth_audit
        and "What has not been proven" in depth_audit
        and "Phase 2B must not begin" in phase2b_checklist,
        results,
    )

    first_candidate = (ROOT / "docs" / "PHASE_2B_FIRST_DRILL_CANDIDATE.md").read_text()
    phase2b_design = (ROOT / "docs" / "PHASE_2B_FORK_EXECUTION_DESIGN.md").read_text()
    template = (ROOT / "docs" / "templates" / "MANUAL_LIVE_FORK_SMOKE_RESULT_TEMPLATE.md").read_text()
    dummy_intent = LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-design-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="local-fork-design",
    )
    execute_raises_unsupported = False
    try:
        EvmForkExecutionArena().execute_local_intent(dummy_intent)
    except RuntimeError as exc:
        execute_raises_unsupported = str(exc) == UNSUPPORTED_EXECUTABLE_FORK_DRILLS
    _check(
        "Phase 2B remains gated",
        default_fork_execution_mode() == ForkExecutionMode.DISABLED
        and execute_raises_unsupported
        and "defaults to disabled" in phase2b_design
        and "Not an exploit" in first_candidate
        and "Do not include upstream RPC URLs" in template,
        results,
    )

    _check(
        "Phase 2A.2 safe output checks",
        "LOCAL_FORK_UNAVAILABLE" in phase2a2_check_output
        and "Read-only discovery: full" in phase2a2_aave_output
        and "Executable drills ran: no" in phase2a2_aave_output
        and _safe(phase2a2_check_output + "\n" + phase2a2_aave_output),
        results,
    )

    capability = (ROOT / "docs" / "CAPABILITY_STATUS.md").read_text()
    _check(
        "Gated adapter honesty",
        "EVM Fork Twin read-only/gated planning" in capability
        and "Sui State Twin" in capability
        and "real Haedal adapter" in capability,
        results,
    )
    _check(
        "Safety report sanitizer",
        _safe(
            main_summary
            + "\n"
            + aave_summary
            + "\n"
            + phase2a_summary
            + "\n"
            + haedal_summary
            + "\n"
            + phase2a2_check_output
            + "\n"
            + phase2a2_aave_output
            + "\n"
            + phase2b_preflight_output
        ),
        results,
    )

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
