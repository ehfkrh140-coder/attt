# v0.1.0 Release Checklist

Use this checklist before treating the MockArena MVP as release-ready.

- [ ] `pytest -q` passes.
- [ ] `python main.py` runs.
- [ ] `python scripts/run_protocol_twin.py --protocol mock_lending` runs.
- [ ] `python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum` handles missing-root or gated status safely.
- [ ] `python scripts/run_protocol_twin.py --protocol haedal` returns unsupported Sui adapter status safely.
- [ ] `python scripts/verify_mvp.py` runs.
- [ ] GitHub Actions `tests` workflow is green.
- [ ] README quick start works.
- [ ] Beginner runbook exists.
- [ ] Capability status exists.
- [ ] MockArena-only executable status is clear.
- [ ] EVM Fork Twin is read-only/gated, not executable.
- [ ] Sui State Twin is unsupported/gated.
- [ ] Real Aave adapter is not implemented.
- [ ] Real Haedal adapter is not implemented.
- [ ] No public network transaction broadcast exists.
- [ ] No real private keys exist.
- [ ] No raw reusable calldata appears in reports.
- [ ] No unsafe artifacts appear in CLI output.
- [ ] Protocol Twin / External World Twin limitations are documented.
- [ ] Twin Fidelity Score appears in beginner-facing output.
- [ ] Version marker exists and matches `pyproject.toml`.

## Release scope

v0.1.0 is a MockArena MVP baseline. It supports local executable mock drills, Protocol Twin onboarding scaffold, External World Twin local emulation, scorecards, Twin Fidelity Score, safe summaries, tests, and CI visibility.

It does not implement executable EVM fork Red drills, a real Aave adapter, a Sui State Twin adapter, or a real Haedal adapter.

## Phase 2A read-only checks

- [ ] EVM read-only client accepts local fork RPC settings only.
- [ ] EVM read-only client exposes no send transaction methods.
- [ ] Aave V3 root-address resolver builds a partial read-only `TargetProtocolSpec`.
- [ ] Aave V3 read-only CLI output says executable drills did not run.
- [ ] Aave V3 read-only CLI output says execution is gated.
- [ ] Phase 2A smoke check appears in `python scripts/verify_mvp.py` output.

## Phase 2A.1 read-only transport checks

- [ ] `adapters/evm_json_rpc_transport.py` allows only read-only local JSON-RPC methods.
- [ ] `EvmReadonlyClient` supports fixture mode and local transport mode.
- [ ] Aave V3 resolver uses safe named calls, not report-visible raw calldata.
- [ ] `python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum --root-address <root-address> --local-rpc-url http://127.0.0.1:8545` reports either read-only discovery or `LOCAL_FORK_UNAVAILABLE` safely.
- [ ] Phase 2A.1 does not execute EVM Red drills or silently fall back to MockArena.
- [ ] `python scripts/verify_mvp.py` includes the Phase 2A.1 fixture smoke check and does not require Anvil or Hardhat.

## Phase 2A.2 live local fork smoke checks

- [ ] `python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545` reports reachable or `LOCAL_FORK_UNAVAILABLE` safely.
- [ ] `python scripts/aave_readonly_discovery.py --root-address <root-address> --local-rpc-url http://127.0.0.1:8545` reports read-only discovery, partial discovery, or unavailable safely.
- [ ] Aave read-only discovery does not use MockArena fallback.
- [ ] Smoke scripts do not send transactions, do not use signing keys, and do not require a live fork for CI.

## Phase 2A read-only workflow checks

- [ ] Local fork check reports PASS, BLOCKED, or UNAVAILABLE with no traceback.
- [ ] Aave read-only discovery reports full, partial, unavailable, or missing-root.
- [ ] Optional target export keeps `authorized_scope=false` and `scope_confirmed=false`.
- [ ] Reports contain selected Red drill recommendations as gated, not executed.
- [ ] Phase 2B remains documented as future work.

## Phase 2A QA checks

- [ ] `docs/PHASE_2A_DEPTH_AUDIT.md` distinguishes fixture-backed CI from optional live local fork testing.
- [ ] `docs/PHASE_2B_READINESS_CHECKLIST.md` exists and blocks executable fork work until prerequisites are complete.
- [ ] `scripts/manual_live_fork_smoke.py` is optional and not run by CI.
- [ ] Manual smoke output remains read-only and safe.
- [ ] Reports do not contain Aave selectors or raw calldata.

## Phase 2B design-only checks

- [ ] Fork execution policy defaults to disabled.
- [ ] EVM fork execution arena is placeholder-only.
- [ ] `execute_local_intent` raises `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.
- [ ] First drill candidate is harmless and non-fund-moving.
- [ ] CI does not run live fork execution.

## Phase 2B Preflight Support

Phase 2B is still blocked and design-only. The new live-smoke support tools help a reviewer record manual read-only evidence before any future execution work is considered.

- `python scripts/record_live_fork_smoke_result.py ...` writes a safe markdown record from reviewed local-only fields.
- `python scripts/phase2b_preflight.py` checks that the manual smoke record, reviewed target manifest, and dependency graph review exist.
- The preflight is expected to report `Phase 2B readiness: FAIL` until every review artifact is present.
- Fork execution remains disabled by default, no transactions are sent, and executable EVM fork Red drills remain unsupported.
- Do not include upstream endpoints, secrets, reusable payloads, or raw selectors in any preflight artifact.
