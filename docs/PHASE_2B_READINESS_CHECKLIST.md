# Phase 2B Readiness Checklist

Phase 2B must not begin until all checks below are complete.

- [ ] Live local fork manual smoke has been run by the user.
- [ ] Local fork read-only discovery works against a real fork.
- [ ] Aave root address is documented by a user-provided target manifest.
- [ ] Discovered Aave contracts and categories have been reviewed.
- [ ] Dependency graph review is done.
- [ ] SafetyGuard has a fork-execution mode design.
- [ ] Transaction execution remains local-only and arena-mediated.
- [ ] Red and Blue never connect to public RPC.
- [ ] No private keys are required or stored.
- [ ] Rollback/snapshot plan exists for every executable fork test.
- [ ] Initial fork execution drill is harmless and value=0.
- [ ] Defense action is mock/local circuit breaker only.
- [ ] Reports still avoid raw calldata, selectors, and reusable transaction payloads.
- [ ] CI continues to run fixture-backed tests without requiring a live fork.

If any item is incomplete, stay in read-only Phase 2A.


## Compatibility checklist tokens

These short checklist phrases are kept for existing release checks.

- [ ] manual_live_fork_smoke_result.md exists
- [ ] Reviewed target manifest exists
- [ ] Explicit enable flag is absent by default

## Concrete design gates added before implementation

- [ ] `manual_live_fork_smoke_result.md` exists and is reviewed.
- [ ] Reviewed target manifest exists.
- [ ] Dependency graph review exists.
- [ ] Fork execution policy has been reviewed.
- [ ] First drill candidate has been approved.
- [ ] Explicit enable flag is absent by default.
- [ ] CI still does not run live fork execution.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS` until implementation approval.

## Live-smoke support preflight gates

- [ ] `scripts/record_live_fork_smoke_result.py` created a safe smoke record.
- [ ] `scripts/phase2b_preflight.py` reports missing prerequisites until review
  artifacts exist.
- [ ] `docs/PHASE_2B_PREFLIGHT.md` has been read by the reviewer.
- [ ] Target manifest remains unconfirmed unless a reviewer confirms scope.
- [ ] Fork execution mode is still disabled by default.
- [ ] `EvmForkExecutionArena.execute_local_intent` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

## Phase 2A.5 evidence and review gates

- [ ] Live local fork evidence pack generated from localhost and reviewed.
- [ ] Fixture-only evidence explicitly rejected for Phase 2B readiness.
- [ ] Read-only TargetProtocolSpec manifest candidate reviewed.
- [ ] Generated manifest does not auto-confirm scope.
- [ ] Dependency graph review candidate generated from Recon and reserve metadata.
- [ ] Manual live fork smoke result recorded and reviewed.
- [ ] Phase 2B preflight run against evidence pack, manifest, and dependency review.
- [ ] Preflight output reviewed as review-ready only.
- [ ] Preflight output is not execution-enabled.
- [ ] Fork execution mode remains disabled.
- [ ] EvmForkExecutionArena still raises unsupported for local execution.

## Phase 2A.5-R reframe gates before Phase 2B

Phase 2A.5-R does not open Phase 2B. It adds role definitions, policy models,
and tests so that a future Phase 2B can be extreme, realistic, and sealed.

- [ ] `docs/SAFETY_BOUNDARY_MODEL.md` has been reviewed.
- [ ] `ForbiddenOutsideModeledInsideMatrix` has been reviewed.
- [ ] Every forbidden external capability has a sealed-lab modeled equivalent.
- [ ] Recon is accepted as a first-class adversarial discovery engine.
- [ ] Red is accepted as a sealed-lab adversarial executor.
- [ ] Blue is accepted as a blind but powerful sealed-lab defender.
- [ ] `docs/NO_FAKE_SCENARIO_STANDARD.md` has been reviewed.
- [ ] Narrative-only Recon findings are rejected.
- [ ] Narrative-only Red drills are rejected.
- [ ] Alert-only Blue responses are rejected when block/quarantine is required.
- [ ] Evaluator verdicts require state-diff or invariant-diff evidence.
- [ ] UI-hidden status alone is rejected as a security boundary.
- [ ] Canonical asset identity failures are represented as invariant failures.
- [ ] Multi-pool same-pattern findings are represented as campaign risk.
- [ ] No live exploit code, public-network procedure, raw calldata, transaction
  bundle, or real-key support has been introduced.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6 evidence quality gates before Phase 2B

Phase 2A.6 improves review quality only. It does not enable execution.

- [ ] `docs/live_fork_evidence_quality_report.md` has been generated and reviewed.
- [ ] Evidence source is classified as fixture-backed, live-local,
  live-local-unavailable, missing, or unknown.
- [ ] Fixture-only evidence is rejected for Phase 2B execution readiness.
- [ ] Missing live-local evidence is recorded as a review finding or blocker.
- [ ] ABI/decode gaps are recorded as triage items.
- [ ] Reserve coverage gaps are recorded.
- [ ] Dependency graph review gaps are recorded.
- [ ] Target manifest review gaps are recorded.
- [ ] Phase 2B blockers remain visible.
- [ ] No Phase 2A.6 verdict grants execution permission.
- [ ] `LIVE_READONLY_EVIDENCE_REVIEW_READY` is treated as review-ready only.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6-H1 source format and Unicode hygiene gates

Phase 2A.6-H1 is hygiene only. It does not enable execution.

- [ ] Critical Python files are readable multi-line source.
- [ ] Critical Markdown files are readable multi-line docs.
- [ ] Critical docs/source contain no hidden bidirectional Unicode controls.
- [ ] Generated reports have visible section headings.
- [ ] Hygiene checks do not alter Phase 2B execution state.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6-Live Review gates before Phase 2B

Phase 2A.6-Live Review consumes user-provided localhost artifacts only. It does
not run discovery automatically and does not enable execution.

- [ ] Live artifact bundle manifest references local files only.
- [ ] Artifact directory review reads files only.
- [ ] Unsafe artifacts are blocked and not printed into reports.
- [ ] Fixture-backed artifacts are not treated as execution-ready.
- [ ] Live-local read-only artifacts are treated as review-ready only.
- [ ] Bundle review can feed the existing evidence quality review path.
- [ ] Bundle reports state execution permission is not granted.
- [ ] No public RPC, transaction sending, or private key path is introduced.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6-RP review packet governance gates before Phase 2B

Phase 2A.6-RP is governance and CI-hardening only. It adds review packets and a
verification gate, but it does not approve execution.

- [ ] `docs/CODEX_PR_REVIEW_PROTOCOL.md` has been read.
- [ ] `docs/reviews/PHASE_2A6_RP_REVIEW_PACKET.md` passes the verifier.
- [ ] `.github/pull_request_template.md` requires compact review packet fields.
- [ ] Review packet claims are independently checked against files, tests, and CI.
- [ ] Review packet states that it is a guide, not proof by itself.
- [ ] Review packet includes reviewer focus map and remaining gaps.
- [ ] No review packet can grant execution permission.
- [ ] No review packet can change Phase 2B status.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6-OP operator guide gates before Phase 2B

Phase 2A.6-OP adds operator guidance, a manual checklist, and deterministic safe
sample artifacts. It does not approve execution.

- [ ] `docs/PHASE_2A6_OPERATOR_GUIDE.md` has been read.
- [ ] `docs/PHASE_2A6_MANUAL_REVIEW_CHECKLIST.md` has been completed by reviewer.
- [ ] Sample bundle review passes by artifact directory when the live bundle reviewer is present.
- [ ] Sample bundle review passes by bundle manifest when the live bundle reviewer is present.
- [ ] Sample bundle reports remain sanitized.
- [ ] Review success is not treated as execution permission.
- [ ] No sample artifact is treated as proof of real live-local ABI compatibility.
- [ ] No public RPC Red/Blue execution exists.
- [ ] No executable fork drills exist.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.
