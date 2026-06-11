# Red / Blue Capability Matrix — Phase 2A.5-R

## ForbiddenOutsideModeledInsideMatrix

Forbidden capabilities are not missing features. They are forbidden externally and modeled internally.

| Public-world behavior | Status outside | Sealed-lab equivalent | Current status |
|---|---|---|---|
| public network active probing | Forbidden | local active probing inside sealed fork/twin | future gated |
| public network transaction broadcast | Forbidden | arena-mediated local fork/local validator execution | future gated |
| public RPC Red/Blue execution | Forbidden | local RPC/fork/validator execution after gates | future gated |
| live victim targeting | Forbidden | synthetic victim accounts and manifest-scoped target twins | model/review |
| public mempool observation | Forbidden | local mempool, ordering, congestion, private-orderflow twins | local modeling |
| real private key usage | Forbidden | deterministic ephemeral lab signers and local impersonation | future gated |
| real fund movement | Forbidden | synthetic balances and local state-diff balances | model/review |
| out-of-scope exploration | Forbidden | manifest-scoped adversarial universe exploration | model/review |
| replayable exploit package | Forbidden | non-portable Red intent specs and sanitized traces | model/review |
| raw calldata / transaction bundle output | Forbidden | internal-only trace with sanitized evidence output | model/review |
| public-network portable exploit artifacts | Forbidden | state-diff and invariant-diff evidence | model/review |

## Role split

| Role | Must be strong at | Must not receive/do |
|---|---|---|
| Recon | finding testable risk surfaces and evidence requirements | public active probing or narrative-only findings |
| Red | local-only invariant pressure and measurable state transitions | public exploit recipes or live execution |
| Blue | blind detection and local emergency containment | Red labels, exact Red path, or public intervention |
| Evaluator | state-diff and invariant-diff scoring | text-only verdicts |
