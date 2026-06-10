# DeFi Defense Simulation Lab — Phase 2A.5 Handoff
_Last updated: 2026-06-10_

이 문서는 새 GPT 채팅과 새 Codex 세션에 프로젝트 상태를 정확히 인수인계하기 위한 문서입니다.  
이 프로젝트는 **공용 네트워크 공격 도구가 아니라**, 완전히 격리된 로컬 환경에서 DeFi 방어 시스템의 유효성을 검증하는 **대학 연구용 방어 검증 프레임워크**입니다.

---

## 0. 새 세션에서 가장 먼저 이해해야 할 것

이 프로젝트의 목표는 단순히 Blue Defender Bot을 만드는 것이 아닙니다.

우리가 계속 고집한 핵심은 다음입니다.

```text
강한 Recon
→ 절묘한 Red Team
→ Blind Blue Defense
→ State-diff / Invariant Evaluation
→ Evidence Pack / Review Workflow
```

Blue가 강하다고 주장하려면, Red가 실제로 어렵고, Recon이 실제 위험 표면을 찾아야 합니다.  
텍스트 시나리오나 정적인 가상 공격 설명만으로는 방어 능력을 증명할 수 없습니다.

하지만 동시에 이 프로젝트의 안전 경계는 절대적입니다.

```text
금지:
- public network transaction broadcast
- public mempool front-running
- real private key
- real fund movement
- public RPC directly used by Red/Blue
- raw reusable calldata in reports
- public-network portable exploit artifacts
- scope 밖 contract targeting
```

허용되는 것은 오직 다음입니다.

```text
- MockArena 안의 실행형 local drill
- localhost EVM fork read-only discovery
- local-only evidence workflow
- gated / disabled Phase 2B execution design
- fixture-backed CI verification
- user-run optional live local fork smoke
```

---

## 1. 프로젝트 정체성

정확한 정체성:

> **DeFi Defense Simulation Lab**은 지정된 DeFi 프로토콜 또는 Protocol Twin을 대상으로, 로컬 격리 환경에서 Recon / Red / Blue / Evaluation을 실행하여 방어 시스템의 유효성을 검증하는 연구 프레임워크다.

현재 repository:

```text
https://github.com/ehfkrh140-coder/attt
```

현재까지의 실질적 상태:

```text
MockArena MVP: 완료
Protocol Twin / External World Twin: 완료
EVM Fork Twin read-only path: Phase 2A.5까지 완료
Aave V3 reserve-aware read-only discovery: 완료
Evidence pack / preflight review workflow: 완료
Phase 2B executable fork execution: 아직 차단 / design-only
Haedal / Sui State Twin: 아직 미구현 / gated
```

---

## 2. 우리가 겪은 설계 전환

초기에는 Red/Blue/Auditor 구조를 논의했습니다.  
하지만 사용자는 곧 중요한 문제를 지적했습니다.

```text
단순 가상 시나리오는 의미가 없다.
실제 프로토콜의 온체인 상태를 로컬에 복제한 실험실이 필요하다.
```

이때 핵심 개념이 정리되었습니다.

```text
EVM Fork Twin
= 실제 EVM 프로토콜의 온체인 상태를 로컬 fork에 복제한 실험실

External World Twin
= fork만으로 복제되지 않는 mempool, keeper, oracle update, user burst, congestion 등을 로컬에서 재현하는 외부환경 트윈

Twin Fidelity Score
= 무엇을 복제했고, 무엇을 에뮬레이션했고, 무엇은 아직 빠졌는지를 정직하게 점수화하는 체계
```

중요한 한계도 명확히 했습니다.

EVM fork는 다음을 자동으로 완전히 복제하지 않습니다.

```text
- live public mempool
- external keeper behavior
- future oracle updates
- offchain APIs
- bridge remote chain state
- frontend behavior
- liquidation / arb bot timing
- network congestion
```

그래서 우리는 다음 원칙을 세웠습니다.

```text
Protocol Twin만으로는 부족하다.
Protocol Twin + External World Twin + Evidence/Fidelity Report가 필요하다.
```

---

## 3. 지금까지의 핵심 개발 단계

### P1 — SafetyGuard / Containment

목표:

```text
강한 Red를 넣기 전에 절대 arena 밖으로 못 나가게 막는다.
```

구현된 핵심:

```text
- public chain id 차단
- chain_id 0 전역 허용 제거
- tx.value == 0 강제
- out-of-scope target 차단
- scope_confirmed 요구
- DefenseExecutor도 SafetyGuard 통과
- Red/Blue raw provider 사용 금지 테스트
- report sanitizer 강화
- EVM/Sui adapter gated
```

---

### P2 — Blind Blue Observables

목표:

```text
Blue가 Red의 정답 라벨을 보지 못하게 한다.
```

P2 이전 Blue는 다음 같은 라벨을 볼 위험이 있었습니다.

```text
oracle_divergence
price_sensitive_withdrawal
liquidity_shock
vault_accounting_pressure
```

이후 Blue는 blind feature만 봅니다.

```text
target_category
call_shape
sender_profile
gas_profile
timing_pattern
dependency_context
state_delta_hint
visibility_mode
local_ordering_hint
```

---

### P3 — Independent Red Drills

목표:

```text
Red drill이 OracleDivergenceDrill 이름만 바꾼 껍데기가 아니게 한다.
```

독립 구현된 핵심 drill:

```text
- LiquidityShockDrill
- VaultAccountingDrill
- MultiStageDrill
```

각 drill은 고유 invariant와 state transition을 갖도록 개선되었습니다.

---

### P4 — Adversarial Evaluation Ordering

목표:

```text
Evaluation이 Blue를 봐주지 않게 한다.
```

추가된 ordering modes:

```text
defense_first
red_first
gas_priority
private_orderflow
randomized_seeded
```

중요 원칙:

```text
defense_first 하나만 통과했다고 Blue score가 1.0이 되면 안 된다.
```

---

### P5 — Target-specific Recon

목표:

```text
Recon이 mock://vault hard-code에서 벗어나 TargetProtocolSpec을 읽고 graph/invariant/hypothesis를 생성하게 한다.
```

구현된 핵심:

```text
AttackSurfaceMap
ContractGraph
DependencyGraph
InvariantSpec
RiskHypothesis
RedDrillRecommendation
BlueControlRecommendation
```

---

### P6 — Context-aware Blue

목표:

```text
Blue가 blind feature만 보는 것이 아니라 Recon context와 arena state를 함께 보게 한다.
```

Blue context에는 다음이 들어갑니다.

```text
ReconReport
AttackSurfaceMap
DependencyGraph
RiskHypotheses
Invariants
ordering_mode
visibility_mode
current_state
recent_state_window
pending_feature_count
```

---

### P7 — Scorecards / Regression / CI

목표:

```text
Blue 점수와 Evaluation 정직성을 분리한다.
```

Score dimensions:

```text
ReconScore
RedScore
BlueScore
SafetyScore
EvaluationQualityScore
```

GitHub Actions도 추가되었습니다.

```text
pip install -e ".[test]"
pytest -q
python main.py
python scripts/verify_mvp.py
```

---

### P8 / P9 — Beginner docs, release verification

목표:

```text
초보자도 README/runbook만 보고 실행 상태를 이해할 수 있게 한다.
```

추가된 것:

```text
docs/BEGINNER_RUNBOOK.md
docs/CAPABILITY_STATUS.md
docs/RELEASE_CHECKLIST.md
VERSION = 0.1.0
scripts/verify_mvp.py
```

---

## 4. Protocol Twin / External World Twin로의 전환

사용자가 매우 중요한 지적을 했습니다.

```text
나는 Aave-like mock profile을 만들 능력이 없다.
대상 프로토콜을 완벽하게 복제하는 방식이 필요하다.
```

이에 따라 방향을 바꿨습니다.

기존 보조 방향:

```text
Aave-like MockArena profile
```

새 핵심 방향:

```text
EVM Fork Twin
= 실제 EVM protocol state를 local fork에 복제

External World Twin
= fork가 복제하지 못하는 외부 환경을 local-only로 에뮬레이션
```

---

## 5. Phase 2A — EVM Fork Twin Read-only Path

Phase 2A는 EVM fork에서 **읽기만 하는 단계**입니다.

절대 하지 않는 것:

```text
- transaction sending
- private key
- Red drills on Aave
- public mempool defense
- executable fork attack
```

### Phase 2A.1 — JSON-RPC read-only transport

구현:

```text
adapters/evm_json_rpc_transport.py
adapters/evm_readonly_client.py
adapters/evm_call_builder.py
```

허용 RPC:

```text
eth_chainId
eth_getCode
eth_call
eth_getStorageAt
eth_getBalance
net_version
web3_clientVersion
```

차단:

```text
eth_sendTransaction
eth_sendRawTransaction
eth_sign
personal_sign
wallet_*
personal_*
debug_*
txpool_*
anvil_set*
hardhat_set*
evm_set*
```

---

### Phase 2A.2 — local fork smoke UX

추가된 스크립트:

```text
scripts/check_local_evm_fork.py
scripts/aave_readonly_discovery.py
scripts/manual_live_fork_smoke.py
```

사용자는 local fork가 있다면 다음을 실행할 수 있습니다.

```bash
python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545
python scripts/aave_readonly_discovery.py --root-address <root-address> --local-rpc-url http://127.0.0.1:8545
python scripts/manual_live_fork_smoke.py --local-rpc-url http://127.0.0.1:8545 --root-address <root-address>
```

fork가 없으면 `LOCAL_FORK_UNAVAILABLE`은 안전한 실패입니다.

---

### Phase 2A.QA — depth audit

문서:

```text
docs/PHASE_2A_DEPTH_AUDIT.md
```

명확히 분리:

```text
CI fixture-backed tests가 증명한 것
사용자 live fork에서 아직 증명해야 할 것
Phase 2B 전에 반드시 필요한 것
```

---

### Phase 2B design-only

문서/코드:

```text
core/fork_execution_policy.py
arenas/evm_fork_execution_arena.py
docs/PHASE_2B_FORK_EXECUTION_DESIGN.md
docs/PHASE_2B_FIRST_DRILL_CANDIDATE.md
docs/PHASE_2B_READINESS_CHECKLIST.md
```

중요:

```text
EvmForkExecutionArena.execute_local_intent()
→ UNSUPPORTED_EXECUTABLE_FORK_DRILLS raise
```

즉, 실행은 아직 막혀 있습니다.

---

## 6. Phase 2A.4 — Aave V3 reserve-aware read-only discovery

Aave V3 read-only discovery는 처음에 core contract만 읽었습니다.

```text
PoolAddressesProvider
Pool
PoolConfigurator
PriceOracle
ACLManager
```

이후 Phase 2A.4에서 reserve-aware discovery로 확장되었습니다.

읽는 safe label:

```text
aave_pool_get_reserves_list
aave_pool_get_reserve_data
aave_pool_get_configuration
aave_oracle_get_asset_price
aave_oracle_get_source_of_asset
aave_acl_get_pool_admin_role
aave_acl_get_risk_admin_role
```

추가된 모델:

```text
targets/aave_v3_readonly.py

AaveV3CoreContracts
AaveV3ReserveSnapshot
AaveV3ReadOnlyDiscoveryReport
```

Aave reserve metadata가 다음 경로로 흐릅니다.

```text
EvmCallBuilder
→ EvmReadonlyClient
→ AaveV3Resolver
→ AaveV3ReadOnlyDiscoveryReport
→ TargetProtocolSpec.protocol_metadata
→ ReconEngine
→ AutoSimulationRunner / CLI / export manifest
```

Recon은 이제 다음을 볼 수 있습니다.

```text
reserve_asset
a_token
stable_debt_token
variable_debt_token
reserve_oracle_source
reserve_paths
debt_paths
reserve_oracle_paths
watch_items
```

새 watch item / risk type:

```text
reserve_configuration_review
price_source_review
unresolved_reserve_fields_watch
reserve_oracle_dependency
reserve_debt_token_dependency
```

중요:

```text
max_reserves default = 8
hard cap = 50
unresolved fields = failure가 아니라 watch item
```

---

## 7. Phase 2A.5 — Live Fork Evidence Pack & Review Workflow

Phase 2A.5의 목적:

```text
read-only discovery 결과를 review 가능한 evidence pack으로 남긴다.
그 evidence pack, target manifest, dependency graph review를 Phase 2B preflight가 소비한다.
```

새 패키지:

```text
evidence/
├─ __init__.py
└─ live_fork_evidence.py
```

새 evidence 모델:

```text
LocalForkCheckEvidence
AaveReadOnlyDiscoveryEvidence
TargetManifestReviewEvidence
DependencyGraphReviewEvidence
LiveForkEvidencePack
```

새 스크립트:

```text
scripts/generate_live_fork_evidence_pack.py
scripts/generate_dependency_graph_review.py
scripts/review_target_manifest.py
```

증거 흐름:

```text
check_local_evm_fork.py
→ aave_readonly_discovery.py
→ LiveForkEvidencePack
→ target manifest export
→ dependency graph review
→ phase2b_preflight.py
→ verify_mvp.py
```

중요한 안전 원칙:

```text
fixture evidence는 CI용이다.
fixture evidence만으로 Phase 2B에 갈 수 없다.
live local fork evidence는 user-run/manual review가 필요하다.
review는 execution permission이 아니다.
```

---

## 8. 현재 최신 GitHub 상태

최근 주요 PR 흐름:

```text
PR #20
- Aave V3 reserve metadata initial work
- reserve list / reserve data discovery
- protocol_metadata
- basic Recon reserve integration

PR #21
- Phase 2A.4 Completion
- full safe call catalog
- max_reserves default 8 / hard cap 50
- discovery report
- config / price / source attempts
- watch items
- Recon watch item consumption
- CLI/export/report improvements

PR #22
- Phase 2A.5 evidence workflow
- evidence package
- evidence pack generator
- dependency graph review generator
- target manifest review
- phase2b_preflight evidence consumption

PR #23
- docs cleanup
- removed accidental GitHub conflict URL from docs/PHASE_2A_DEPTH_AUDIT.md
- added docs hygiene test
```

Latest verified status:

```text
PR #23 merged
GitHub Actions tests workflow success
```

---

## 9. 현재 지원되는 것

Supported now:

```text
MockArena executable local simulation
Blind Blue defense
Independent Red drills in MockArena
Multi-mode evaluation
Scorecards
SafetyGuard and report sanitizer
Protocol Twin scaffold
External World Twin concepts
Twin Fidelity Score
EVM local read-only JSON-RPC transport
Aave V3 core + reserve read-only discovery
Aave reserve metadata → Recon integration
Live fork evidence pack workflow
Target manifest review
Dependency graph review
Phase 2B preflight review gate
GitHub Actions CI
Beginner runbook
```

---

## 10. 아직 지원되지 않는 것

Not supported yet:

```text
Executable EVM fork Red drills
Actual local fork transaction execution
Live fork mempool defense
Real Aave defense bot
Real public network execution
Real private key support
Real fund movement
Haedal/Sui State Twin
Sui/Move localnet adapter
```

현재 모든 Aave 관련 기능은:

```text
read-only discovery
planning
review
evidence
preflight
```

까지입니다.

---

## 11. 현재 검증 명령

기본 검증:

```bash
pytest -q
python main.py
python scripts/verify_mvp.py
```

MockArena simulation:

```bash
python scripts/run_protocol_twin.py --protocol mock_lending
```

Aave fixture read-only discovery:

```bash
python scripts/aave_readonly_discovery.py --root-address aave-root --fixture-readonly
python scripts/run_protocol_twin.py --protocol aave_v3 --network ethereum --root-address aave-root --fixture-readonly
```

Aave evidence pack fixture generation:

```bash
python scripts/generate_live_fork_evidence_pack.py --fixture-readonly --root-address aave-root --output /tmp/aave_v3_evidence_pack.md --export-target /tmp/aave_v3_readonly.yaml --export-dependency-review /tmp/dependency_graph_review.md
python scripts/review_target_manifest.py --target /tmp/aave_v3_readonly.yaml
python scripts/generate_dependency_graph_review.py --target /tmp/aave_v3_readonly.yaml --output /tmp/dependency_graph_review_review.md
python scripts/phase2b_preflight.py --evidence-pack /tmp/aave_v3_evidence_pack.md --target-manifest /tmp/aave_v3_readonly.yaml --dependency-graph-review /tmp/dependency_graph_review.md
```

Live local fork optional commands:

```bash
python scripts/check_local_evm_fork.py --local-rpc-url http://127.0.0.1:8545
python scripts/aave_readonly_discovery.py --root-address <AAVE_POOL_ADDRESSES_PROVIDER> --local-rpc-url http://127.0.0.1:8545 --max-reserves 8
python scripts/manual_live_fork_smoke.py --local-rpc-url http://127.0.0.1:8545 --root-address <AAVE_POOL_ADDRESSES_PROVIDER>
```

---

## 12. 다음 권장 단계

다음 단계는 바로 Phase 2B execution이 아닙니다.

추천 다음 단계:

```text
Phase 2A.6 — Live Fork Evidence Quality & ABI Compatibility Review
```

목표:

```text
evidence pack / exported manifest / dependency graph review를 입력으로 받아
read-only discovery의 품질을 평가하고,
ABI compatibility / decode quality / reserve coverage / blocker를 정리한다.
```

왜 필요한가:

```text
현재까지는 fixture-backed evidence가 강하다.
하지만 실제 local fork에서 Aave ABI와 decoding이 충분히 맞는지 아직 증명되지 않았다.
```

Phase 2A.6에서 만들 것:

```text
EvidenceQualityScore
ABICompatibilityReport
DiscoveryTriageReport
ReserveCoverageReport
Phase2BBlockerSummary
```

입력:

```text
evidence pack markdown
exported target manifest
dependency graph review
optional manual live fork smoke result
```

출력:

```text
docs/live_fork_evidence_quality_report.md
or user-specified safe markdown path
```

여전히 금지:

```text
No transactions
No private keys
No Red drills on Aave
No Phase 2B execution
No public RPC from bots
```

---

## 13. 새 GPT 채팅 시작 문구

새 GPT 대화 시작 시 아래를 붙여넣으세요.

```text
나는 GitHub repo `https://github.com/ehfkrh140-coder/attt`에서 DeFi Defense Simulation Lab을 개발 중입니다.

첨부한 `DeFi_Defense_Simulation_Lab_Phase_2A5_Handoff_2026-06-10.md`를 먼저 읽고 현재 상태를 이어받아 주세요.

중요:
- 이 프로젝트는 공용 네트워크 공격 도구가 아닙니다.
- MockArena MVP는 완료되었습니다.
- Aave V3 EVM Fork Twin은 현재 read-only discovery / evidence workflow 단계입니다.
- Phase 2B executable fork execution은 아직 차단되어 있습니다.
- 최신 상태는 PR #23 cleanup까지 반영된 상태입니다.
- 다음 권장 단계는 `Phase 2A.6 — Live Fork Evidence Quality & ABI Compatibility Review`입니다.

먼저 아래 섹션으로 현재 상태를 요약해 주세요.

[프로젝트 상태 10줄 요약]
[현재 지원되는 것]
[아직 지원되지 않는 것]
[가장 중요한 안전 경계]
[다음 단계 후보]
[추천하는 다음 Codex 요청 방향]
```

---

## 14. 새 Codex 세션 첫 메시지

Codex는 로컬 첨부 MD를 직접 읽지 못할 수 있습니다.  
따라서 이 MD 파일을 GitHub repository의 `docs/` 아래에 커밋한 뒤, Codex에게 그 경로를 읽으라고 해야 합니다.

Codex 첫 메시지:

```text
Before coding, read this handoff document in the repository:

docs/DeFi_Defense_Simulation_Lab_Phase_2A5_Handoff_2026-06-10.md

Do not start implementation until you summarize it.

After reading it, respond with:

1. Project identity
2. Current implemented state
3. Current safety boundaries
4. What Phase 2A.5 completed
5. What remains unsupported
6. Why Phase 2B execution is still blocked
7. Recommended next step

Important:
- Do not implement anything yet.
- Do not modify code yet.
- Do not enable Phase 2B.
- Do not send transactions.
- Do not add private keys.
- Do not add public RPC.
- First summarize the handoff and propose the next work plan.

The expected next phase is likely:

Phase 2A.6 — Live Fork Evidence Quality & ABI Compatibility Review

But first read the handoff and confirm.
```

---

## 15. 이 MD 파일을 GitHub에 올리는 방법

PowerShell 기준:

```powershell
cd C:\Users\qhrb9\Desktop\attt

git checkout main
git pull --ff-only

git checkout -b docs/phase-2a5-handoff

# 다운로드한 MD 파일을 아래 경로로 복사
# docs\DeFi_Defense_Simulation_Lab_Phase_2A5_Handoff_2026-06-10.md

git status --short

git add docs\DeFi_Defense_Simulation_Lab_Phase_2A5_Handoff_2026-06-10.md
git commit -m "Add DeFi defense lab Phase 2A.5 handoff"
git push -u origin docs/phase-2a5-handoff
```

그 다음 GitHub에서 PR을 만들고 merge합니다.

Merge 후 Codex에게는 위 14번 메시지를 보냅니다.

---

## 16. 새 채팅 / 새 Codex로 넘어가기 전 체크리스트

```text
1. 이 MD 파일 다운로드
2. 새 GPT 채팅에 첨부
3. 이 MD 파일을 GitHub docs/에 커밋
4. PR 생성 및 merge
5. Codex에게 docs 경로 읽게 하기
6. Codex가 요약할 때까지 코드 수정 금지
7. 새 GPT에게 Phase 2A.6 설계를 요청
```

---

## 17. 앞으로의 운영 원칙

Codex는 빠르고 강합니다.  
하지만 잘하려면 다음을 명확히 줘야 합니다.

```text
1. 이번 단계의 목표
2. 데이터 흐름
3. 반드시 생겨야 할 파일
4. 반드시 연결돼야 할 모듈
5. 하면 안 되는 것
6. 얕은 구현 거부 조건
7. 테스트
8. GitHub Actions 확인
```

이제부터는 작은 단계가 아니라 큰 스프린트로 가도 됩니다.

단, 패턴은 유지합니다.

```text
큰 기능 스프린트
→ QA / gap closure
→ evidence / review workflow
→ next design
```

현재 다음 추천은:

```text
Phase 2A.6 — Live Fork Evidence Quality & ABI Compatibility Review
```

