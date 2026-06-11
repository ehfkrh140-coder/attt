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
- [ ] Fixture-only evidence is explicitly treated as not execution-ready.
- [ ] Missing live local evidence is reported honestly as a finding or blocker.
- [ ] ABI compatibility and decode findings are triaged.
- [ ] Reserve coverage gaps are scored and reported.
- [ ] Dependency graph review gaps are reported.
- [ ] Target manifest review gaps are reported.
- [ ] Report output is sanitized and contains no reusable public-network artifact.
- [ ] Final verdict is one of:
  - `REVIEW_INCOMPLETE`
  - `FIXTURE_ONLY_NOT_EXECUTION_READY`
  - `LIVE_READONLY_EVIDENCE_REVIEW_READY`
  - `BLOCKED_FOR_PHASE_2B`
- [ ] No Phase 2A.6 verdict grants execution permission.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6-H1 source format and Unicode hygiene gates

Phase 2A.6-H1 is still review-only. It hardens source and documentation
integrity, but grants no execution permission.

- [ ] Critical Python files are readable multi-line source files.
- [ ] Critical markdown files are readable multi-line documents.
- [ ] Critical source/docs contain no hidden bidirectional Unicode controls.
- [ ] Critical generated report has visible section headings.
- [ ] Missing evidence artifacts are handled safely.
- [ ] Malformed target manifests are handled safely.
- [ ] Unknown evidence sources are handled safely.
- [ ] Live-readonly review-ready wording cannot be mistaken for execution approval.
- [ ] Fixture-backed evidence remains not execution-ready.
- [ ] Report output contains no raw calldata, selectors, transaction bundles,
  secrets, upstream RPC URLs, or portable exploit artifacts.
- [ ] Phase 2B execution remains disabled.
- [ ] `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

If any item is incomplete, stay in Phase 2A review/design mode.

## Phase 2A.6-Live Review gates before Phase 2B

Phase 2A.6-Live Review is still read-only and review-only. It helps reviewers
assess user-provided localhost artifacts without enabling executable fork drills.

- [ ] `docs/PHASE_2A6_LIVE_ARTIFACT_REVIEW.md` has been read.
- [ ] User-provided artifact bundle references local files only.
- [ ] Bundle review reports missing artifacts honestly.
- [ ] Bundle review marks fixture-backed artifacts as not execution-ready.
- [ ] Bundle review marks localhost read-only artifacts as review-ready only.
- [ ] Unsafe artifacts are blocked without printing unsafe contents.
- [ ] Safe evidence pack, target manifest, and dependency graph inputs feed the
  existing Phase 2A.6 evidence-quality reviewer.
- [ ] No bundle verdict grants execution permission.
- [ ] No public RPC Red/Blue path is introduced.
- [ ] No live discovery runs unless a reviewer explicitly runs a read-only
  localhost command outside CI.
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
