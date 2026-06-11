# Safety Boundary Model — Phase 2A.5-R

## Permanent principle

**External public-world behavior is forbidden. Internal sealed-lab equivalents must be modeled with maximum realism.**

**외부 세계에서는 금지한다. 내부 실험실에서는 현실과 똑같이, 오히려 더 극한적으로 구현한다.**

**Red가 최강이려면 Recon은 더 최강이어야 한다.**

**For Red to be world-class, Recon must be stronger than Red.**

This project forbids public-world side effects. It does **not** forbid extreme adversarial capability inside a sealed local lab. Strong local adversarial pressure is required for meaningful defense validation.

## Permanent forbidden outside the sealed lab

These are not missing features. They are permanently forbidden outside the sealed lab:

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

## ForbiddenOutsideModeledInsideMatrix

| Forbidden outside | Modeled inside the sealed lab |
|---|---|
| public network active probing | local active probing inside sealed fork/twin |
| public network transaction broadcast | arena-mediated sealed local fork / local validator execution after gating |
| public RPC Red/Blue execution | local RPC / local fork / local validator execution after gating |
| live victim targeting | synthetic victim accounts and manifest-scoped target twins |
| public mempool observation | local mempool twin, local ordering twin, congestion twin, private orderflow twin |
| real private key usage | lab-only deterministic ephemeral signers and local impersonation |
| real fund movement | synthetic balances, local fork balances, state-diff fund movement |
| out-of-scope exploration | manifest-scoped adversarial universe exploration |
| replayable exploit package | non-portable Red intent specs and sanitized traces |
| raw calldata / transaction bundle output | internal-only execution trace with sanitized evidence output |
| public-network portable exploit artifacts | state-diff and invariant-diff evidence |

## Current Phase 2A limitations

- Aave/EVM fork work remains read-only discovery, planning, evidence, and review.
- Red Team executable fork drills are not enabled.
- Blue does not operate as a public-network bot.
- No transaction-sending path is added by this phase.
- `EvmForkExecutionArena.execute_local_intent()` must continue to raise `UNSUPPORTED_EXECUTABLE_FORK_DRILLS`.

## Future sealed-local permissions after explicit gates

Future PRs may model stronger sealed-local capabilities only after review gates exist:

- snapshot/revert-controlled local active probing
- local-only transaction simulation
- local-only synthetic account/mint construction
- local-only dependency failure pressure
- local-only adversarial ordering and private-orderflow simulation
- local-only emergency Blue response actions

Those future capabilities must remain manifest-scoped, local-only, sanitized, non-portable, and evidence-driven.
