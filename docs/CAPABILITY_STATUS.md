# Capability Status

| Capability | Status | Notes |
|---|---|---|
| MockArena executable simulation | Supported | Current v0.1.0 MVP runtime for local state-changing drills |
| MockArena executable drills | Supported | Current MVP runtime for local state-changing drills |
| Blind Blue defense | Supported | Uses blind features and no Red answer labels |
| Multi-mode evaluation | Supported | defense_first, red_first, gas_priority, private_orderflow, randomized_seeded |
| Protocol Twin onboarding scaffold | Supported | Distinguishes MockArena, EVM Fork Twin, and Sui State Twin modes |
| External World Twin local emulation | Supported | Emulates orderflow, keepers, oracle timing, liquidity, bridge stubs, offchain stubs, user intents, and network conditions |
| Twin Fidelity Score | Supported | Reports copied/emulated/missing coverage honestly |
| Scorecards | Supported | Recon, Red, Blue, Safety, and Evaluation quality scores |
| GitHub Actions CI | Supported | Runs install, pytest, main demo, and MVP verifier |
| Beginner-safe CLI summary | Supported | `main.py` and verifier output are sanitized |
| EVM Fork Twin read-only/gated planning | Partial / Gated | Aave V3 path is recognized, but executable fork drills are blocked until adapter readiness |
| Aave V3 fork-twin onboarding path | Partial / Gated | Uses EVM Fork Twin path and never silently falls back to mock |
| EVM Fork adapter | Gated / Not implemented | Placeholder only; executable support is blocked until a real isolated adapter exists |
| Sui Localnet adapter | Gated / Not implemented | Placeholder only; executable support is blocked until a real isolated adapter exists |
| executable EVM fork Red drills | Unsupported / Not implemented | Intentionally gated for this release |
| real Aave adapter | Unsupported / Not implemented | Future work only; not part of v0.1.0 |
| Sui State Twin | Unsupported / Not implemented | Gated until a real Sui adapter exists |
| real Haedal adapter | Unsupported / Not implemented | Future work only; not part of v0.1.0 |
| Haedal path | Gated / Not implemented | Sui state twin adapter is not implemented |
| Public network execution | Not supported | Intentionally forbidden by the safety boundary |
| Real private keys | Not supported | Intentionally forbidden by the safety boundary |
| EVM Fork Twin read-only discovery scaffold | Supported | Validates local fork settings and performs safe read-only discovery |
| Aave V3 root-address read-only resolver | Supported | Discovers Pool, PoolConfigurator, PriceOracle, and ACLManager when local read data is available |
| Recon on read-only TargetProtocolSpec | Supported | Runs Recon on partial read-only EVM target specs |
| live fork mempool defense | Unsupported / Not implemented | Future phase only |
| real transaction execution | Unsupported / Not implemented | Intentionally blocked |
| real Aave defense bot | Unsupported / Not implemented | Future phase only |
| EVM local JSON-RPC read-only transport | Supported in Phase 2A.1 | Localhost-only reads: chain id, code, read-only calls, storage, and balance. |
| Aave V3 local-fork read-only discovery | Partial / Gated | Requires a user-provided local fork and root address; executable drills remain gated. |
| Executable Aave fork drills | Not implemented | Phase 2A.1 is read-only only. |
| Local fork transaction sending | Not supported | Read-only transport blocks send, sign, wallet, debug, txpool, and local mutation RPC methods. |
| Local fork smoke script | Supported in Phase 2A.2 | Checks localhost fork reachability using read-only calls only. |
| Aave V3 read-only discovery script | Supported in Phase 2A.2 | Requires local fork plus root address; reports partial/unavailable safely. |
| Live local fork transactions | Not supported | Smoke tooling is read-only and keeps execution gated. |
| Safe read-only target export | Supported in Phase 2A | Exports unconfirmed Aave read-only TargetProtocolSpec manifests without executable scope. |
| Phase 2B executable fork drills | Future work | Not implemented in Phase 2A; local fork execution remains gated. |
| Phase 2A depth audit | Supported | Documents fixture-backed CI, optional live local fork manual checks, and remaining limits. |
| Manual live local fork smoke | Optional / Manual | User-run localhost-only read-only smoke; not run by CI. |
| Phase 2B readiness checklist | Supported | Blocks executable fork work until live read-only and safety prerequisites are reviewed. |
| Phase 2B fork execution design | Design only | Policy and Arena interfaces exist, but execution is disabled. |
| EVM fork execution arena | Gated placeholder | `execute_local_intent` raises unsupported until Phase 2B approval. |
| First harmless fork drill candidate | Design only | Snapshot/revert and liveness sentinel; no asset movement. |

## Phase 2B Preflight Support

Phase 2B is still blocked and design-only. The new live-smoke support tools help a reviewer record manual read-only evidence before any future execution work is considered.

- `python scripts/record_live_fork_smoke_result.py ...` writes a safe markdown record from reviewed local-only fields.
- `python scripts/phase2b_preflight.py` checks that the manual smoke record, reviewed target manifest, and dependency graph review exist.
- The preflight is expected to report `Phase 2B readiness: FAIL` until every review artifact is present.
- Fork execution remains disabled by default, no transactions are sent, and executable EVM fork Red drills remain unsupported.
- Do not include upstream endpoints, secrets, reusable payloads, or raw selectors in any preflight artifact.

## Phase 2A.4 Read-only Aave Reserve Metadata

Aave V3 read-only discovery now attempts to read reserve metadata from the local fork after the PoolAddressesProvider resolves the Pool. The resolver asks only safe named read calls for the reserve list, per-reserve data, reserve configuration, asset price, oracle source, and ACL role labels, then feeds the discovered reserve assets, aToken/debt-token relationships, watch items, and basic configuration flags into Recon.

The default reserve limit is 8. A user may request a different limit, but the resolver enforces a hard cap of 50 and reports whether truncation occurred. Discovery may be full, partial, decode-unavailable, or unavailable depending on what the local fork returns. The result is still read-only: no transactions are sent, Red drills are recommendation-only, MockArena is not used as Aave fallback, and Phase 2B execution remains blocked.

## Phase 2A.5 evidence workflow status

- Live local fork evidence pack: available as a read-only review workflow.
- Fixture evidence pack: available for CI and release verification only; it is not enough for Phase 2B.
- Target manifest review: parses generated manifests and checks read-only flags, but does not confirm scope automatically.
- Dependency graph review: generated from Recon output and reserve metadata; it is a review candidate, not execution permission.
- Phase 2B execution: still blocked and disabled. No transactions are sent and no Aave Red drills run.

## Phase 2A.5-R Recon / Red / Blue Extreme Capability Reframe

Phase 2A.5-R reframes Recon, Red Team, and Blue Team capabilities without
opening Phase 2B. It documents that public-world side effects are forbidden while
sealed-lab equivalents may be modeled only after explicit gates.

Capability | Status | Notes
--- | --- | ---
Recon capability boundary | Supported / Policy | Recon is a first-class adversarial discovery engine, not a report generator
Red Team capability boundary | Supported / Policy | Red is a sealed-lab adversarial executor, not a story generator
Blue Team capability boundary | Supported / Policy | Blue is blind but can model strong local defensive actions
ForbiddenOutsideModeledInsideMatrix | Supported / Policy | Forbidden public capabilities are modeled internally only after gates
No-Fake-Scenario standard | Supported / Policy | Narrative-only findings, drills, defenses, and verdicts are insufficient
Phase 2B execution | Blocked | The reframe does not enable executable fork drills

## Permanent forbidden capabilities

The following remain permanently forbidden outside the sealed lab:

- public network active probing
- public network transaction broadcast
- public RPC through Red/Blue execution
- live victim targeting
- public mempool observation for attack discovery
- real private key usage
- real fund movement
- out-of-scope contract/program exploration
- replayable exploit package generation
- raw reusable calldata / transaction bundle output
- public-network portable exploit artifacts

These are forbidden outside and may only be modeled inside a sealed local lab
after the relevant future gates are approved.

## Current Phase 2A limitations

Phase 2A remains read-only/review-only for EVM fork paths. It supports MockArena
execution, read-only local fork discovery, evidence pack generation, manifest
review, dependency review, preflight review, and review packets. It does not
support executable EVM fork Red drills, real transaction sending, public RPC
Red/Blue execution, private keys, real fund movement, live Aave bots, or public
mempool behavior.

## Future sealed-local capabilities after explicit gates

Future sealed-local capabilities may include snapshot/revert-controlled active
probing, local-only transaction simulation, local-only signer use, local-only
impersonation, synthetic accounts/mints, local ordering pressure, private
orderflow simulation, and local emergency defense actions. They require a
separate approved Phase 2B or later PR and remain blocked in this PR.

## Phase 2A.6 Live Fork Evidence Quality & ABI Compatibility Review

Phase 2A.6 reviews the quality of Phase 2A.5 evidence artifacts. It scores or
triages evidence completeness, ABI/decode quality, reserve coverage, dependency
review quality, target manifest review quality, and Phase 2B blockers.

Capability | Status | Notes
--- | --- | ---
Evidence quality report | Supported / Review-only | Produces sanitized markdown findings
ABI compatibility report | Supported / Review-only | Records decode success and unavailable fields
Reserve coverage report | Supported / Review-only | Reports reserve count, truncation, and unresolved fields
Discovery triage report | Supported / Review-only | Converts gaps into review items
Phase 2B blocker summary | Supported / Review-only | Keeps blockers visible and cannot approve execution
Execution-ready verdict | Unsupported | No Phase 2A.6 verdict grants execution permission

## Phase 2A.6-H1 Source Format Integrity & Hidden Unicode Hygiene

Phase 2A.6-H1 hardens source and documentation readability. It rejects hidden
bidirectional Unicode controls in critical docs/source, keeps generated reports
readable, and does not change runtime permissions.

Capability | Status | Notes
--- | --- | ---
Critical source/doc line-count checks | Supported | Prevents unreadable single-line blobs
Hidden bidi-control scan | Supported | Does not ban normal Korean text or ordinary Unicode punctuation
Report heading checks | Supported | Keeps generated review reports readable
Phase 2B execution | Blocked | Hygiene checks do not enable execution

## Phase 2A.6-Live Review capability status

Phase 2A.6-Live Review consumes user-provided localhost artifacts only. It does
not run discovery automatically, does not connect to public RPC, and does not
send transactions.

Capability | Status | Notes
--- | --- | ---
Live artifact bundle convention | Supported / Review-only | Local file references only
Bundle manifest review | Supported / Review-only | Reads manifest paths, does not run discovery
Artifact directory review | Supported / Review-only | Classifies conventional filenames
Fixture-demo bundle review | Supported / CI-only | Deterministic, not execution-ready
Live-local read-only classification | Supported / Review-only | Requires localhost/read-only indicators
Unsafe artifact blocking | Supported | Unsafe contents are not printed into reports
Evidence quality integration | Supported / Review-only | Feeds safe inputs into existing Phase 2A.6 reviewer
Phase 2B execution | Blocked | No executable fork drills are enabled

## Phase 2A.6-RP review packet governance status

Phase 2A.6-RP adds a required Codex PR review packet protocol and verifier. It
is governance and CI-hardening only. It does not change runtime permissions.

Capability | Status | Notes
--- | --- | ---
Codex PR Review Packet protocol | Supported | Falsifiable review guide required for future PRs
Review packet verifier | Supported | Local packet and local GitHub event payload modes
PR template review checklist | Supported | Compact review packet fields in PR body
Reviewer focus map | Supported | Changed files prioritized for inspection
Claims-to-verify section | Supported | Packet states what reviewers verify independently
Phase 2B execution | Blocked | Review governance does not enable execution

Review packets reduce reviewer burden but do not replace independent review,
GitHub diff inspection, CI logs, or direct source inspection.

## Phase 2A.6-OP operator guide and sample bundle status

Phase 2A.6-OP adds operator guidance, a manual review checklist, and deterministic
safe sample artifacts. It is review-only and does not change execution permissions.

Capability | Status | Notes
--- | --- | ---
Phase 2A.6 operator guide | Supported / Review-only | Localhost artifact preparation workflow
Manual review checklist | Supported / Review-only | Reviewer sign-off without execution approval
Deterministic safe sample bundle | Supported / CI-safe | Sample files only, not real user evidence
Sample bundle manifest review | Supported / Review-only | Uses the Phase 2A.6 live artifact bundle reviewer when present
Current PR review packet | Supported | Verified by the review packet verifier when present
Phase 2B execution | Blocked | Operator guidance does not enable execution

The sample bundle does not prove live local fork ABI compatibility and does not
claim Phase 2B readiness.
