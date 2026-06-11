# Capability Status

This page summarizes supported, gated, and unsupported capabilities for the
DeFi Defense Simulation Lab.

The project remains a defensive, isolated research framework. It is not a
public-network attack tool and it is not a text-only scenario generator.


## Compatibility status tokens

The following compact status rows are kept for existing release checks.

Capability | Status | Notes
--- | --- | ---
MockArena executable drills | Supported | Contained local runtime
Scorecards | Supported | Recon, Red, Blue, Safety, Evaluation
EVM Fork adapter | Gated / Not implemented | Execution blocked
Sui Localnet adapter | Gated / Not implemented | Execution blocked
Public network execution | Not supported | Forbidden by safety boundary
Real private keys | Not supported | Forbidden by safety boundary
EVM Fork Twin read-only/gated planning | Partial / Gated | Read-only Aave path
executable EVM fork Red drills | Unsupported / Not implemented | Phase 2B gated
Sui State Twin | Unsupported / Not implemented | Future work only
real Aave adapter | Unsupported / Not implemented | Future work only
real Haedal adapter | Unsupported / Not implemented | Future work only
Aave V3 fork-twin onboarding path | Partial / Gated | Read-only, no fallback

## Core supported capabilities

- **MockArena executable simulation:** supported for local state-changing drills.
- **MockArena executable drills:** supported in the contained mock runtime.
- **Blind Blue defense:** supported with blind features and no Red answer labels.
- **Multi-mode evaluation:** supports `defense_first`, `red_first`,
  `gas_priority`, `private_orderflow`, and `randomized_seeded`.
- **Protocol Twin onboarding scaffold:** distinguishes MockArena, EVM Fork Twin,
  and Sui State Twin modes.
- **External World Twin local emulation:** models orderflow, keepers,
  oracle timing, liquidity, bridge stubs, offchain stubs, user intents,
  and network conditions.
- **Twin Fidelity Score:** reports copied, emulated, and missing coverage.
- **Scorecards:** reports Recon, Red, Blue, Safety, and Evaluation quality.
- **GitHub Actions CI:** runs install, tests, main demo, and MVP verification.
- **Beginner-safe CLI summary:** `main.py` and verifier output are sanitized.

## EVM / Aave read-only support

- **EVM Fork Twin read-only planning:** supported as a gated read-only path.
- **Aave V3 fork-twin onboarding path:** supported without mock fallback.
- **EVM local JSON-RPC read-only transport:** localhost-only reads for chain id,
  code, read-only calls, storage, and balance.
- **Aave V3 root-address read-only resolver:** discovers core contracts when
  local read data is available.
- **Aave V3 reserve-aware discovery:** reads reserve metadata through safe
  named read calls only.
- **Recon on read-only TargetProtocolSpec:** supported for partial read-only
  EVM target specs.
- **Safe read-only target export:** exports unconfirmed Aave read-only manifests
  without executable scope.
- **Local fork smoke script:** supported as read-only localhost smoke tooling.
- **Manual live local fork smoke:** optional and user-run; CI does not require it.

## Unsupported or gated capabilities

- **Executable EVM fork Red drills:** unsupported and gated.
- **Local fork transaction sending:** unsupported; read-only transport blocks
  send, sign, wallet, debug, txpool, and mutation RPC methods.
- **Real transaction execution:** unsupported and intentionally blocked.
- **Live local fork transactions:** unsupported in Phase 2A.
- **Real Aave adapter / defense bot:** future work only.
- **Live fork mempool defense:** future phase only.
- **EVM Fork adapter:** gated placeholder for executable support.
- **Sui Localnet adapter:** gated placeholder for executable support.
- **Sui State Twin / Haedal path:** unsupported until a real Sui adapter exists.
- **Public network execution:** forbidden by the safety boundary.
- **Real private keys:** forbidden by the safety boundary.
- **Real fund movement:** forbidden by the safety boundary.

## Phase 2B Preflight Support

Phase 2B is still blocked and design-only. Live-smoke support tools help a
reviewer record manual read-only evidence before any future execution work.

- `python scripts/record_live_fork_smoke_result.py ...` writes a safe markdown
  record from reviewed local-only fields.
- `python scripts/phase2b_preflight.py` checks that the manual smoke record,
  reviewed target manifest, and dependency graph review exist.
- The preflight is expected to report `Phase 2B readiness: FAIL` until every
  review artifact is present.
- Fork execution remains disabled by default.
- No transactions are sent.
- Executable EVM fork Red drills remain unsupported.
- Do not include upstream endpoints, secrets, reusable payloads, or raw
  selectors in any preflight artifact.

## Phase 2A.4 Read-only Aave Reserve Metadata

Aave V3 read-only discovery reads reserve metadata after the
PoolAddressesProvider resolves the Pool. The resolver uses safe named read calls
for reserve list, reserve data, reserve configuration, asset price, oracle
source, and ACL role labels.

The discovered reserve assets, aToken/debt-token relationships, watch items,
and basic configuration flags flow into Recon.

The default reserve limit is 8. A user may request a different limit, but the
resolver enforces a hard cap of 50 and reports whether truncation occurred.
Discovery may be full, partial, decode-unavailable, or unavailable.

The result is still read-only:

- no transactions are sent
- Red drills are recommendation-only
- MockArena is not used as Aave fallback
- Phase 2B execution remains blocked

## Phase 2A.5 evidence workflow status

- Live local fork evidence pack: available as a read-only review workflow.
- Fixture evidence pack: available for CI and release verification only.
- Fixture evidence is not enough for Phase 2B.
- Target manifest review parses generated manifests and read-only flags.
- Target manifest review does not confirm scope automatically.
- Dependency graph review is generated from Recon output and reserve metadata.
- Dependency graph review is a review candidate, not execution permission.
- Phase 2B execution is still blocked and disabled.
- No transactions are sent and no Aave Red drills run.

## Phase 2A.5-R Recon / Red / Blue Extreme Capability Reframe

The capability model uses this permanent rule:

> External public-world behavior is forbidden.
> Internal sealed-lab equivalents must be modeled with maximum realism.

> 외부 세계에서는 금지한다.
> 내부 실험실에서는 현실과 똑같이, 오히려 더 극한적으로 구현한다.

> Red가 최강이려면 Recon은 더 최강이어야 한다.

> For Red to be world-class, Recon must be stronger than Red.

Forbidden public-world capabilities are not missing features. They are
**forbidden outside** and **modeled inside** through sealed-lab equivalents.

### Permanent forbidden capabilities

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

### Current Phase 2A limitations

- EVM fork and Aave V3 remain read-only discovery, planning, evidence,
  and preflight review.
- Red can execute MockArena drills, but executable EVM fork Red drills remain
  disabled.
- Blue can defend in local arenas and consume blind observables.
- Blue does not operate as a public-network bot.
- Phase 2B execution remains blocked.
- `EvmForkExecutionArena.execute_local_intent()` still raises
  `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

### Future sealed-local capabilities after explicit gates

- Recon may support snapshot/revert-controlled local active probing,
  local-only transaction simulation, synthetic account/mint construction,
  dependency failure construction, and adversarial external-world discovery.
- Red may support sealed local fork execution, local-only signer use,
  impersonation, synthetic attacker assets, manifest-scoped stale targets,
  local-only campaigns, adversarial ordering, and private-orderflow simulation.
- Blue may support local-only pause, quarantine, circuit breakers,
  dependency isolation, emergency governance simulation, risk parameter updates,
  vault outflow guards, canonical identity enforcement, and incident evidence.

These future capabilities are policy and design targets only until a separate
Phase 2B PR explicitly opens the sealed execution harness.

## Phase 2A.6 Live Fork Evidence Quality & ABI Compatibility Review

Phase 2A.6 adds a read-only evidence quality review layer over the Phase 2A.5
evidence workflow. It consumes an evidence pack, exported target manifest,
dependency graph review, optional manual live fork smoke record, and optional
Phase 2B preflight output.

Supported in Phase 2A.6:

- evidence source classification
- evidence completeness findings
- ABI compatibility and decode quality review
- Aave reserve coverage scoring and gap triage
- dependency graph review quality checks
- target manifest review quality checks
- Phase 2B blocker summary
- optional Phase 2B preflight output as review evidence only
- safe markdown output at `docs/live_fork_evidence_quality_report.md`

Still not supported:

- executable EVM fork Red drills
- transaction sending
- private key support
- public RPC Red/Blue execution
- Aave Red drills
- live Raydium/Solana/Aave interaction
- execution-ready verdicts

Phase 2A.6 verdicts are review verdicts only:

- `REVIEW_INCOMPLETE`
- `FIXTURE_ONLY_NOT_EXECUTION_READY`
- `LIVE_READONLY_EVIDENCE_REVIEW_READY`
- `BLOCKED_FOR_PHASE_2B`

There is intentionally no execution-approved verdict. Review success is not
execution permission, and Phase 2B remains disabled.

## Phase 2A.6-H1 Source Format Integrity & Hidden Unicode Hygiene

Phase 2A.6-H1 hardens source and docs integrity.

The hygiene pass confirms:

- critical Python files are normal multi-line source files
- critical markdown files are readable multi-line documents
- critical source/docs contain no hidden bidirectional Unicode control characters
- fixture-only evidence remains not execution-ready
- live-readonly evidence can be review-ready only, never execution-approved
- malformed manifests become safe review findings or blockers
- unknown evidence sources are handled safely
- missing artifacts are reported without failing CI
- generated reports remain sanitized and readable
- Phase 2B execution remains disabled

No public-network execution, private key support, public RPC Red/Blue execution,
Aave Red drills, or executable fork drills are introduced by this hygiene pass.

## Phase 2A.6-Live Review capability status

Phase 2A.6-Live Review adds a safe review pass for user-provided localhost
read-only artifact bundles. It is review-only and does not change execution
permissions.

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

Phase 2A.6-Live Review does not prove that live-local evidence exists unless a
user provides those artifacts. It only classifies and reviews the supplied local
files.
