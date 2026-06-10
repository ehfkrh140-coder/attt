from __future__ import annotations

import subprocess
import sys

import pytest

from arenas.evm_fork_execution_arena import EvmForkExecutionArena, UNSUPPORTED_EXECUTABLE_FORK_DRILLS
from core.fork_execution_policy import (
    ForkExecutionMode,
    ForkExecutionPreconditions,
    default_fork_execution_mode,
    is_fork_execution_allowed,
)
from redteam.local_tx_intent import LocalTxIntent


def design_intent() -> LocalTxIntent:
    return LocalTxIntent(
        target="aave-root",
        function_category="sentinel",
        calldata_label="safe-design-only",
        value=0,
        sender_role="guardian",
        gas_strategy="local-normal",
        safety_scope="local-fork-design",
    )


def test_phase2b_design_doc_exists() -> None:
    text = open("docs/PHASE_2B_FORK_EXECUTION_DESIGN.md").read()
    assert "ForkExecutionSafetyPolicy" in text
    assert "Execution defaults to disabled" in text
    assert "No transaction sending" in text


def test_fork_execution_policy_defaults_disabled() -> None:
    assert default_fork_execution_mode() == ForkExecutionMode.DISABLED
    assert not is_fork_execution_allowed()


def test_fork_execution_preconditions_require_all_gates() -> None:
    assert not ForkExecutionPreconditions().all_gates_satisfied()
    partial = ForkExecutionPreconditions(live_readonly_smoke_passed=True, explicit_user_enable=True)
    assert not is_fork_execution_allowed(ForkExecutionMode.LOCAL_EXECUTION_ENABLED, partial)
    complete = ForkExecutionPreconditions(
        live_readonly_smoke_passed=True,
        target_manifest_reviewed=True,
        dependency_graph_reviewed=True,
        snapshot_plan_present=True,
        rollback_plan_present=True,
        value_zero_enforced=True,
        scope_confirmed=True,
        adapter_ready=True,
        explicit_user_enable=True,
    )
    assert complete.all_gates_satisfied()
    assert is_fork_execution_allowed(ForkExecutionMode.LOCAL_EXECUTION_ENABLED, complete)
    assert not is_fork_execution_allowed(ForkExecutionMode.LOCAL_EXECUTION_DRY_RUN, complete)


def test_evm_fork_execution_arena_execute_raises_unsupported() -> None:
    with pytest.raises(RuntimeError, match=UNSUPPORTED_EXECUTABLE_FORK_DRILLS):
        EvmForkExecutionArena().execute_local_intent(design_intent())


def test_first_drill_candidate_is_harmless() -> None:
    text = open("docs/PHASE_2B_FIRST_DRILL_CANDIDATE.md").read()
    assert "Not an exploit. Not a real attack. Not a fund-moving drill." in text
    for phrase in ["value=0", "No token transfer", "No approval", "No liquidation", "No borrow", "No withdrawal", "No governance execution", "No oracle manipulation", "No asset movement"]:
        assert phrase in text


def test_phase2b_checklist_requires_manual_live_smoke() -> None:
    text = open("docs/PHASE_2B_READINESS_CHECKLIST.md").read()
    assert "manual_live_fork_smoke_result.md exists" in text
    assert "Reviewed target manifest exists" in text
    assert "Explicit enable flag is absent by default" in text
    assert "CI still does not run live fork execution" in text


def test_manual_live_fork_smoke_template_contains_no_secrets() -> None:
    text = open("docs/templates/MANUAL_LIVE_FORK_SMOKE_RESULT_TEMPLATE.md").read().lower()
    assert "upstream rpc url" in text
    for token in ["private_key", "mnemonic", "raw_calldata", "0x026b1d5f"]:
        assert token not in text


def test_docs_do_not_enable_phase2b_execution() -> None:
    docs = open("README.md").read() + open("docs/BEGINNER_RUNBOOK.md").read() + open("docs/PHASE_2B_FORK_EXECUTION_DESIGN.md").read()
    assert "design-only" in docs.lower()
    assert "execute_local_intent()` raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`" in docs
    assert "no executable EVM fork Red drills" in docs or "executable EVM fork Red drills remain blocked" in docs


def test_ci_does_not_run_live_fork_execution() -> None:
    workflow = open(".github/workflows/test.yml").read()
    assert "manual_live_fork_smoke.py" not in workflow
    assert "execute_local_intent" not in workflow
    assert "LOCAL_EXECUTION_ENABLED" not in workflow


def test_verify_mvp_mentions_phase2b_still_gated() -> None:
    output = subprocess.run([sys.executable, "scripts/verify_mvp.py"], check=True, capture_output=True, text=True).stdout
    assert "Phase 2B remains gated: PASS" in output
    assert "Overall: PASS" in output
