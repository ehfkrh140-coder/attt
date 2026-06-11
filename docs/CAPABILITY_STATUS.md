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
- Fixture evidence pack: available for CI and release verification only; it is not enough for Phase 2B.
- Target manifest review: parses generated manifests and checks read-only flags, but does not confirm scope automatically.
- Dependency graph review: generated from Recon output and reserve metadata; it is a review candidate, not execution permission.
- Phase 2B execution: still blocked and disabled. No transactions are sent and no Aave Red drills run.

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
