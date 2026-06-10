# Phase 2B Fork Execution Design

This is a design-only document. It does not enable executable EVM fork drills.

## ForkExecutionSafetyPolicy

Phase 2B execution must be mediated by an Arena and must stay local-only.

Required boundary:

- Local-only execution boundary: bots connect only to localhost or 127.0.0.1.
- No public RPC from Red or Blue.
- No private keys.
- No raw send transactions outside Arena.
- Snapshot before every drill.
- Rollback after every drill.
- `tx.value` must be 0.
- Target must be in confirmed scope.
- Execution requires an explicit enable flag.
- Execution requires a live-readonly-smoke-passed marker.
- Execution requires a reviewed target manifest.
- Execution requires reviewed dependency graph.
- Execution requires adapter readiness.
- Execution defaults to disabled.

## Fork execution modes

- `DISABLED`: default; no execution and no dry-run claims.
- `READ_ONLY_ONLY`: only read-only local fork discovery is allowed.
- `LOCAL_EXECUTION_DRY_RUN`: future design state for validation without state-changing execution.
- `LOCAL_EXECUTION_ENABLED`: future gated state; unavailable until every checklist item is complete.

## Required preconditions

All must be true before local fork execution can be considered:

- `live_readonly_smoke_passed`
- `target_manifest_reviewed`
- `dependency_graph_reviewed`
- `snapshot_plan_present`
- `rollback_plan_present`
- `value_zero_enforced`
- `scope_confirmed`
- `adapter_ready`
- `explicit_user_enable`

## Current implementation status

`core/fork_execution_policy.py` is design-only and defaults to disabled. `arenas/evm_fork_execution_arena.py` exposes the intended method names but `execute_local_intent()` raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

## Non-goals

- No executable EVM fork Red drills in this phase.
- No transaction sending.
- No signing keys.
- No public mempool logic.
- No public RPC bot path.
- No real Aave defense bot.
