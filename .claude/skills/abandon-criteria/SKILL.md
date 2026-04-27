---
name: abandon-criteria
description: 매 phase 시작 시 go 기준뿐 아니라 kill 기준 (abandon triggers) 을 최소 3개 명시적으로 선언하여, 프로젝트가 sunk-cost 로 연장되는 것을 차단한다. phase 진행 중 trigger 발화 여부를 모니터링하고, 발화 시 즉시 중단. v1.2 (2026-04-27): project-type-aware trigger selection (§3.5) — discovery-form vs functional-form vs hybrid 별 trigger archetype 분리.
license: MIT
version: 1.2.0
---

# Abandon Criteria

> 연구/프로덕트 프로젝트에서 Phase 를 거치며 go 기준 (이 신호 이상이면 진행) 은 보통 명시되지만, **kill 기준 (이 신호 이하면 중단)** 은 생략되기 쉽다. 그 결과 Phase 0→1→2→2.5 로 sunk cost 가 누적되고, 근본 premise 재질문은 외부 pressure 없이는 발생하지 않는다.
>
> 근거:
> - [audits/2026-04-25-mirosalmon-abandon-retrospective.md](../../audits/2026-04-25-mirosalmon-abandon-retrospective.md) §4.6 — output drift 실패
> - [audits/2026-04-26-activist-intent-llm-killed-postmortem.md](../../audits/2026-04-26-activist-intent-llm-killed-postmortem.md) — input drift 실패 (framework gap → data-validity category 추가)

## 언제 사용하는가

- **매 Phase 설계 직후, 실행 직전** 필수 invoke
- Pivot 제안 직전 — 새 방향의 abandon 기준도 같이 선언
- reference validation checklist 통과 직후 Phase 0 진입 전

## 선언 규칙

### 1. 최소 수량
Phase 당 **3개 이상**. 적으면 "실패 좁게 정의" 오류.

### 2. 각 trigger 는 아래 4요소 필수
```
1. Trigger name: 
2. Measurable condition (숫자 임계 or binary event): 
3. Data source (어디서 확인): 
4. On-fire action: 즉시 중단 / 교정 phase / scope 축소 / pivot
```

### 3. Trigger 유형 분배 (권장: 4 category 각 ≥ 1)
- **Mechanism trigger** 최소 1개: p-value / effect size / accuracy 같은 내부 지표
- **Product/market trigger** 최소 1개: user interview 결과, reference 사망, market 경쟁자 출현
- **Resource trigger** 최소 1개: 토큰 예산 초과, timeline 초과, attention 초과
- **Data-validity trigger** 최소 1개: input 자료의 가용성/품질 (sample 미달, rater 미확보, pipeline coverage 미달). output trigger 와 별개 — output 평가가 가능하기 *전* 발화 가능해야 함. (Y 2026-04-26 retrospective 후 추가)

### 3.5 Project-type-aware trigger selection (2026-04-27 신설, v1.2)

> 근거: [audits/2026-04-27-project-type-calibration-disclosure-decay-meta-tool.md](../../audits/2026-04-27-project-type-calibration-disclosure-decay-meta-tool.md). disclosure_decay_meta_tool Day 10/13 mechanical fire 가 spec mismatch 였음을 확인.

§3 의 trigger archetype 은 project-type 에 따라 다르게 선택한다 — 분류는 [templates/reference-validation-checklist.md §0.5](../../templates/reference-validation-checklist.md) 에서 수행.

- **Discovery-form 프로젝트**: 위 §3 의 4-category 그대로. Mechanism trigger 는 phenomenon-existence (Welch p / Sharpe / Fleiss κ / R²). 예: X / Y / Z / β2 / Factor / α / F1 / C2.
- **Functional-form 프로젝트**: Mechanism trigger 가 *tool actionability* 형태로 변형 — output differentiation / recommendation reproducibility / layer utility. **Phenomenon-existence trigger 는 upstream-verified component 에 적용 금지** (해당 phenomenon 은 이미 검증됐으므로 우리 trigger 가 발화하면 *우리* 데이터-handling 버그 means, not phenomenon 부재). [templates §4.6](../../templates/reference-validation-checklist.md) catalog 에서 ≥3 추출. 예: disclosure_decay_meta_tool 본체, quant-research-process.
- **Hybrid**: sub-task 별 분리 — discovery sub-task 는 §3 archetype, functional 본체는 §4.6. 예: disclosure_decay_meta_tool 의 LLM ensemble generalization sub-task 는 discovery (Fleiss κ ≥ 0.6 적용), 나머지 cohort matching + NPV calculator 는 functional.

연동: `docs/portfolio-research-rules.md` Gate G + `templates/reference-validation-checklist.md` §0.5 / §4.6.

### 4. 금지 항목
- "결과가 안 좋으면 중단" 같은 subjective trigger 금지. 숫자나 binary event 로만.
- "충분히 해 보고 판단" 금지. trigger 는 선언 시점에 측정 가능해야 한다.
- "다음 phase 에서 재평가" 금지. trigger 는 **현 phase 내** 발화 가능해야 한다.
- **Functional-form 프로젝트의 phenomenon-existence trigger 금지** (위 §3.5). Hybrid 의 discovery sub-task 한정으로만 허용.

## Trigger 카탈로그 (카피 시작점)

### Mechanism triggers
- "effect size < X 에서 n=Y 이상 누적 관측 시 중단"
- "critical metric 의 p > 0.1 에서 Bonferroni 보정 후에도 유의하지 않으면 중단"
- "cross-LLM replication 2개 모델 중 1개라도 실패 시 중단"
- "baseline 이 우리 model 을 능가하면 (단일 조건 아닌 majority) 중단"

### Product/market triggers
- "reference 가 N 주 내 1개 이상의 negative signal 발생 (funding 철회, pivot 발표, 경쟁자 인수 등)"
- "customer interview 에서 '이 문제 해결에 지불 의사 없음' 답변 3/3"
- "경쟁자가 동일 product 를 더 빠르게 출시"
- "regulation/legal 환경 변화로 core assumption 무효화"

### Resource triggers
- "LLM 토큰 예산 $X 초과"
- "human-time N 일 초과"
- "특정 dependency 제거 불가능한 blocker 발견"
- "attention quality 2 세션 연속 저하"

### Data-validity triggers
- "Phase 0 EOD 까지 fetched sample < N" (sample availability — Y 가 이 trigger 사전 등록 안 함)
- "n=N pilot 에서 inter-rater κ < 0.6 또는 single-rater only" (rater methodology — multi-rater 미확보 자체가 trigger)
- "Week W EOD 까지 end-to-end pipeline coverage < X%" (예: CAR computable / output extractable 비율)
- "Critical input data source 의 deprecation / access loss"
- "Domain expert (labeler / annotator) 확보 실패 by deadline"
- "공유 daemon / queue 의 priority 미공개 + capacity probe 미달"

## Phase 감사 통합

모든 phase 감사 문서에 아래 섹션 포함:

```markdown
## Abandon Criteria (선언 + 점검)

### 선언된 triggers (phase 시작 시)
1. Trigger: {name}
   - Category: mechanism / product-market / resource / data-validity
   - Condition: 
   - Source: 
   - Action: 
2. ...
3. ...

### 이번 phase 중 trigger 발화 check
- [ ] Trigger 1 발화: Y / N. Y 면 증거: 
- [ ] Trigger 2 발화: Y / N. 
- [ ] Trigger 3 발화: Y / N.

### 발화 시 조치 실행 여부
- 실행했는가: [ ] Y / [ ] N
- 안 했다면 이유 (sunk cost rationalize 주의): 
```

## 조기 감지 의무

Trigger 발화는 **부정적** 이 아니라 **정보**. 발화했는데도 "그래도 한 번 더" 는 sunk cost 확장. MiroSalmon 에서 반복된 패턴.

- 발화 시 다음 phase 진입 금지
- 중단 / 교정 / pivot 중 **즉시** 선택
- 교정 시에도 새 phase 는 새 abandon criteria 선언 필수

또한 **trigger 가 발화 안 했어도** input 단계 (data validity) 가 깨졌다면 중단/scope 축소 고려. Y 사례: 5 trigger 중 mechanical 발화 0 이지만 sample/rater/coverage 셋 동시 위반으로 결과 평가 자체 무의미 — output-layer trigger 의 사각지대.

## 설치

- 이 파일: `d:\vscode\meta-harness\skills\abandon-criteria\SKILL.md`
- 신규 repo 에 `<repo>/.claude/skills/abandon-criteria/SKILL.md` 로 복사
- `templates/reference-validation-checklist.md` §4 (Phase 별 abandon criteria) + §4.5 (data validity contracts) 와 연동

## Worked Examples

### ✅ 성공 사례 — sin-controversy-pilot (Project α, 2026-04-25)
2일 sacrificial pilot. CLAUDE.md 작성 시점에 단일 metric kill gate 사전 등록:
"in-sample Sharpe > 0.3 → 생존, ≤ 0.3 → 즉시 폐기". n=43 firms · 95 months 측정 결과
Sharpe = -0.490 (가설 부호 반대). **48h 내** 폐기 결정 + ABANDONED.md 작성 + agent 해제.
sign-flip / 조건 변경 / scope 확장 유혹 차단됨.
- 효과 요인:
  - 단일 metric (Sharpe) → 발화 여부 binary
  - 사전 통계적 정당화 ("Sharpe 0.3 미달 시 OOS 검정력 거의 없음")
  - 통과/폐기 양 경로의 산출물 사전 명시 (Y appendix merge / ABANDONED.md retrospective)
  - timebox (2 일) 가 sunk-cost 누적 자체를 차단
- retrospective: `audits/2026-04-25-sin-controversy-pilot-abandon-retrospective.md`

### ❌ 실패 사례 (output drift) — mirosalmon (2026-04-25 retrospective)
Phase 0 → 0.5 → 1 → 2 → 2.5 까지 11일 누적. Go 기준은 명시됐지만 Kill 기준 약함.
Phase 0 말 Stage 3 시점에 "이 결과가 product-valuable 한가?" 질문이 발화돼야 했지만
sunk-cost 합리화로 한 단계씩 더. 결과적으로 thesis 근본 오류는 phase 2.5 에 가서야 표면화.
- retrospective: `audits/2026-04-25-mirosalmon-abandon-retrospective.md` §4.6

### ❌ 실패 사례 (input drift / framework gap) — activist-intent-llm (Project Y, 2026-04-26)
18 시간 single-burst execution. CLAUDE.md 에 abandon criteria 5개 선언했으나 모두 *output
layer*: n<3000, κ<0.5, CI∋0+regime null, budget>$25, short-side infeasible. 실제 실패는
*input layer* — sample availability (20K → 257 = 1.3%), rater methodology (single
non-expert labeler κ=0.52 vs 0.7 target), CAR coverage (100% → 25%). 셋 다 발화 안 한 이유:
선언된 trigger 가 *결과 평가 시점* (κ < 0.5 / CI / regime null) 또는 *절대값 floor* (n<3000)
이라 *target 으로부터의 gap* + *input prerequisite* 을 못 잡음. n=257 < 3000 인데도 "Day 2
EOD" 평가 시점이 모호해 명시 발화 X, κ=0.52 ≥ 0.5 라 #2 발화 X.

- 교훈: data-validity trigger 가 abandon criteria 의 별도 category 여야 함 (위 §3 분배에
  추가됨). Y 는 framework 의 필요 조건 검증 사례 — 사전 등록한 trigger 만으로는 input
  invalidation 사각지대 발생.
- retrospective: `audits/2026-04-26-activist-intent-llm-killed-postmortem.md`

### ✅ Project-type calibration 사례 — disclosure-decay-meta-tool (2026-04-27)

v1 reference-validation 작성 시 sub-agent 가 QR Scout 표준 (discovery-form) trigger 를
functional-form repo 에 그대로 적용 → 두 건의 mechanical fire:

- **Day 10 #3 (hyperbolic α(t)=K/(1+λt) R² ≥ 0.3)**: R² 0.046–0.131 STRICT FAIL.
  진단: arxiv 2512.11913 의 short-horizon crowding 모델을 long-horizon
  publication-decay 에 over-apply 한 spec error. Welch p=0.003 로 phenomenon
  자체는 verified — wrong model form, not absent phenomenon. **Drop from gate
  set → exploratory only.**
- **Day 13 #2 (PnL-vs-LLM Pearson ρ ≥ 0.3)**: max ARI 0.11 / NMI 0.23 / phi 0.11
  STRICT FAIL. 진단: PnL cluster (HOW) ≠ LLM mechanism (WHY) — 두 layer 가 같은
  것을 측정한다고 가정한 것이 spec error. Orthogonality 가 feature, not bug.
  **Reposition as functional gate "F2 PnL layer utility"**: PnL similarity layer 가
  ≥1 downstream functional component (NPV capacity haircut, dashboard
  orthogonality page) 에 non-trivial 변동을 공급하면 PASS. → PASS.

사용자 진단으로 project-type mismatch 표면화. v1.2 가 spec 분리 + 본 레포는
functional-form 으로 재정의 + 7 trigger 중 #1/#2/#3 재분류 (#1 sanity gate /
#2 reposition F2 / #3 dropped → exploratory) → **fire count 0/12 corrected**.

대비 포인트:
| | discovery-form (잘못 적용) | functional-form (정정) |
|---|---|---|
| Trigger #2 fire 조건 | ρ < 0.3 (phenomenon agreement) | layer utility (downstream consumer 존재) |
| Trigger #3 fire 조건 | hyperbolic R² < 0.3 (model fit) | dropped (exploratory only) |
| 발화 시 결정 | scope 축소 또는 kill | spec 보정 + 진행 |
| 근본 원인 | template 의 implicit discovery-only 가정 | type 명시 의무 (§0.5) + functional catalog (§4.6) |

retrospective: `D:\vscode\disclosure_decay_meta_tool\audits\project_type_calibration_2026-04-27.md` (source) /
`audits/2026-04-27-project-type-calibration-disclosure-decay-meta-tool.md` (meta-side handover)

대비 포인트 (전체):
| | sin-controversy-pilot | mirosalmon | activist-intent-llm (Y) | disclosure-decay-meta-tool |
|---|---|---|---|---|
| Kill 기준 사전 명시 | 단일 metric, 숫자 임계 | 약하게 정의 | 5 trigger, 모두 output-layer | 7 trigger, 2개 type-mismatch |
| Project type | discovery (sacrificial) | discovery (research) | discovery (alpha) | **functional + 1 discovery sub-task** |
| Timebox | 2 일 hard | 없음 (phase-by-phase) | 2 weeks scope, 18h burst | 21-day Phase 1 |
| 실제 실패 layer | output (Sharpe sign-flip) | product thesis (reference) | input (data validity) | **spec mismatch (template gap)** |
| 발화 메커니즘 | 사전 등록 mechanical 발화 | sunk-cost 합리화 누적 | mechanical 발화 X (output 사각지대) | mechanical 발화 ✓ but spec 자체가 mis-fit |
| 발화 시 행동 | 즉시 폐기 + ABANDONED.md | "한 번 더" 합리화 누적 | meta-harness 외부 트리거로 kill | type-aware spec 정정 + 진행 (사용자 진단) |
| 결과 | abandon framework 시연 성공 | 11일 + $25 sunk | framework gap (data-validity 추가) | framework gap (project-type 추가) |

## 관련

- `templates/reference-validation-checklist.md` §4, §4.5
- `skills/drift-watchdog/SKILL.md` — Rule 24 (drift 2x 자동 교정 phase) 과 결합
- `audits/2026-04-25-mirosalmon-abandon-retrospective.md` §4.6 — output drift 실패
- `audits/2026-04-26-activist-intent-llm-killed-postmortem.md` — input drift 실패 + framework gap
- `audits/2026-04-25-sin-controversy-pilot-abandon-retrospective.md` — 성공 사례
- `docs/principles.md` §6.8 (Data Validity Contracts)
