# Red Team Capability Boundary — Phase 2A.5-R

## Definition

Red Team = the adversarial executor that consumes Recon findings and attempts to realize them as local-only state transitions under sealed-lab containment.

Red Team is not a story generator. Red Team must attempt local state transitions that challenge protocol invariants.

## Current allowed Red capability

- MockArena executable drills
- local-only Red intent modeling
- fixture-backed adversarial scenarios
- invariant-targeted local state transitions in MockArena

## Future gated Red capability after Phase 2B approval

Documented only; not implemented in Phase 2A.5-R:

- sealed local fork transaction execution
- local-only signer use
- local-only impersonation
- synthetic attacker accounts
- synthetic attacker mints
- manifest-scoped retired/stale target interaction
- local-only multi-pool campaigns
- local-only adversarial ordering
- local-only private orderflow simulation

## Permanently forbidden Red capability

- public network transaction broadcast
- public RPC execution
- live victim targeting
- real private key usage
- real fund movement
- public mempool attack discovery
- scope escape
- replayable exploit output
- raw calldata / transaction bundle reporting
- public-network portable exploit artifacts

## Required Red output

Red output must be:

- non-portable Red intent
- sanitized action trace
- state diff
- invariant impact
- evidence references

Red output must **not** be:

- public exploit recipe
- live reproduction guide
- raw calldata
- transaction bundle
- copy-paste attack script
