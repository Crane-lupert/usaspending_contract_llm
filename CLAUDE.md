# Project M1 — USAspending Federal Contract Narrative LLM

> USAspending.gov federal contract obligation text (정부 contract description 자유 텍스트) × multi-vendor LLM ensemble × forward revenue commitment 추출 → defense/IT contractor next quarter earnings surprise 사전 예측. **β2 frozen 후 swap 1순위 launch 2026-04-27**. **PURE daemon-free** (Gate F ✓), **discovery-form** (Gate G ✓).
>
> Reference validation: `d:/vscode/meta-harness/audits/2026-04-27-usaspending-contract-reference-validation.md`. Phase 0 plan: `d:/vscode/meta-harness/audits/2026-04-27-project-usaspending-contract-phase0-plan.md` (366줄). Overnight prompt v4: `d:/vscode/meta-harness/audits/2026-04-27-project-usaspending-contract-overnight-start-prompt.md` (208줄).

---

## Purpose

USAspending.gov API 의 federal contract obligation text → 3-vendor LLM ensemble 가 *forward revenue commitment* 3-axis (revenue timing / magnitude / cancellation risk) 추출 → defense/IT cross-section *next quarter earnings surprise* 사전 예측. 정부 contract = *committed revenue* (예약된 수입), 회사 8-K announce 전 USAspending 에 raw 노출 = alpha window.

**핵심 가설**: USAspending publish → 회사 8-K announce 까지 lag (보통 며칠~몇 주) 안에서 LLM 이 forward revenue commitment 정량화 → defense/IT contractor cross-section earnings surprise positioning.

**기여**: military spending → defense stock 학술 well-known (Greenwood-Vayanos / Cieslak-Pflueger 류). *forward revenue LLM extraction × cross-section earnings surprise* 결합 + LLM commentary parsing infrastructure 부재 — academic gap medium-strong.

**산업 lead time risk**: Palantir / Booz Allen / Govini 같은 회사 가 이미 USAspending watch 자동화. Phase 1 trigger #2 핵심 — "lag <24h sample 비율 ≥50% OR alpha decay >50%/y → writeup-only freeze (full kill 아님)".

---

## Dependencies (공유 인프라)

- USAspending.gov API 무료 (2008-2026, defense/IT R&D-intensive R1000 firm universe ~수십만 contract awards/y subset)
- Compustat XRD/SALE (R&D-intensive filter, free-tier 활용)
- yfinance (price + quarterly earnings, free)
- OpenRouter: `shared_utils.openrouter_client.OpenRouterClient(project="usaspending_contract_llm")`, project cap=$35 (max=8). Coord registered 2026-04-27T21:30 (mailbox in_reply_to `20260427T1604-usaspending_contract_llm-001`).
- Atomic IO: `shared_utils.atomic_io.atomic_write_json + FileLock`
- **SEC daemon 사용 X** (Gate F ✓). filer_ontology / daemon-capacity-probe 도 미사용
- 체크포인트: 매일 `portfolio-coordination/checkpoints/<date>/usaspending.md`
- Mailbox: `D:/vscode/portfolio-coordination/mailbox/usaspending_contract_llm/`

---

## Phase Scope

### Phase 0 — Week 1 (Day 1-7)
- Day 1: repo init + manifest skeleton + USAspending API client skeleton + arxiv/SSRN 신규 paper 사전 조사 + Gate F 재확인
- Day 2-3: small sample fetch (defense/IT R&D-intensive R1000 firms × 1y = ~20K-30K contract awards)
- Day 4: 3-vendor LLM ensemble n=20 oracle pilot (3-axis schema)
- Day 5: Fleiss κ ≥0.6 verify
- Day 6: n=10 full-pipeline dry-run + **USAspending publish lag 측정** (며칠~몇 주 distribution, 산업 lead time 비교 baseline)
- **Day 7 EOD 단일 kill gate (6 AND)**: sample ≥20K + dry-run ≥7/10 + 3-axis Fleiss κ ≥0.6 + spend ≤$8 + scoop 미발견 + publish lag 측정 OK (5-bin distribution + <24h / <7d 비율 측정)

### Phase 1 — Week 2-3 (Day 8-21)
- Day 8-12: full sample LLM inference + applicant→ticker mapping
- Day 13-15: cross-section quarterly earnings surprise + **realistic execution audit (lag 반영, 산업 alpha decay 측정)**
- Day 16-18: rigor pass (FDR, DSR, bootstrap, contamination)
- Day 19-20: Streamlit dashboard + writeup
- Day 21: hard cap

---

## Day-by-Day Gate (요약)

- Day 1 EOD: API skeleton + scoop 사전 조사
- Day 5 EOD: sample ≥20K + dry-run ≥5/10 + κ initial measure
- **Day 7 EOD: 단일 kill gate 6 AND**
- Day 14 EOD: cross-section quarterly earnings surprise initial measure + lag 반영 alpha
- **Day 17 EOD: 산업 lead time gate measure** (Phase 1 #2)
- Day 21 EOD: hard cap

Y kill 의 18시간 single-burst 패턴 회피 — daily checkpoint + self-audit + abandon mechanical + realistic execution audit 4중 안전망.

---

## Abandon Criteria (4-category, Phase 별 ≥3)

상세: reference-validation §4.

### Phase 0
1. **[Data-validity]** Day 5 EOD sample fetch < 20K → fetch retry / R&D quartile→quintile 1회만, 미달 시 중단
2. **[Mechanism]** Day 6 n=20 pilot Fleiss κ < 0.6 → 3-axis → 2-axis 단순화 1회만, 재미달 시 중단
3. **[Data-validity]** Day 6 publish lag 측정 실패 (5-bin distribution 불가 OR <24h 비율 unable to determine) → spec 수정 1회만, 재미달 시 중단
4. **[Resource]** Phase 0 spend > $8 → Phase 1 진입 보류
5. **[Product-market]** **arxiv/SSRN "USAspending LLM cross-section earnings", "federal contract forward revenue extraction" 신규 paper 출현** → 즉시 중단

### Phase 1 (reframed 2026-04-27 — alpha-discovery + robustness section structure)

**Single hard kill** = trigger #1. Trigger #2 demoted to *paper §4 robustness finding* (cohort heterogeneity is itself an identification result, not a freeze condition).

1. **[Mechanism] HARD KILL** — Day 14 mid-checkpoint, ALL 3 metric AND fail:
   - incremental R² over CCM aggregate < 5%, AND
   - quarterly earnings surprise ROC-AUC < 0.6, AND
   - cross-section quintile spread Sharpe (XAR/XLK-hedged) < 0.3
   → ABANDONED.md (no paper headline). 1 of 3 fail → exploratory; 2 of 3 fail → tighten + re-test once.
2. **[Mechanism] §4 ROBUSTNESS finding** (not kill) — Day 16 cohort-stratified evaluation: USAspending → 8-K lag <24h sample fraction trajectory + alpha decay rolling-Sharpe by cohort. Reported in paper §4 as *time-varying alpha + industry-absorption mechanism* (Cotropia 2017 USPTO pattern). Heterogeneity = identification strength, not weakness.
3. **[Resource]** Day 21 EOD hard cap
4. **[Data-validity]** Final analyzable sample < 1,500 firm-quarter cells → power 부족, writeup-only with caveat
5. **[Product-market]** mailbox portfolio overlap signal → orthogonality test
6. **[Mechanism]** Cross-LLM replication: 3-vendor 중 2개 이상 부호 불일치 → mechanism unstable → ABANDONED.md

---

## Realistic Execution Audit (M1 특수)

**핵심 risk**: USAspending publish 시점 vs 회사 8-K announce 시점 vs 산업측 (Palantir / Booz Allen / Govini) 추격 시간 lag. naive backtest 가 *production-grade* X 이라면 academic alpha 약화.

### Audit spec
1. **USAspending publish timestamp** = USAspending API record date + announce date 의 ≥2 일치 시점
2. **8-K announce timestamp** = SEC EDGAR (read-only API, daemon X) 의 회사별 next earnings 8-K date
3. **Lag distribution** = 5-bin (≤24h / 1-3d / 3-7d / 1-2w / >2w). <24h 비율 high → 산업측 이미 활용 → alpha 약함
4. **Alpha decay 측정** = 2008-2014 vs 2015-2020 vs 2021-2026 cohort 의 alpha magnitude 변화율 (산업 추격 효과)
5. **통과 조건**: lag <24h 비율 <50% AND alpha decay <50%/y → published claim 가능

상세: phase0-plan §Realistic Execution Audit.

---

## Inter-Repo Mailbox

QR Scout 멤버 간 파일 메시지 버스. 가입 사유: shared-utils + buy-side weapon + cross-repo coordination.

- Inbox: `D:/vscode/portfolio-coordination/mailbox/usaspending_contract_llm/`
- 절차: `D:/vscode/portfolio-coordination/mailbox/SCHEMA.md`
- 자동 감지: SessionStart + UserPromptSubmit hook
- 가입 5단계: `d:/vscode/meta-harness/templates/qr-scout-mailbox-onboarding.md`

처리: 응답 도입부 "📬 처리: N건" (0건 생략). 발신: `mailbox/<target>/<ISO>-usaspending_contract_llm-<slug>.md`. **금지**: secret / .env / API key.

---

## 통계 Rigor Checklist

- [ ] IS/OOS: 2008-2018 IS, 2019-2026 OOS (frozen)
- [ ] FDR (3-axis × 3-horizon × sector = ~12 검정)
- [ ] Deflated Sharpe Ratio
- [ ] Bootstrap CI B=1000, cluster by quarter
- [ ] Newey-West 표준오차
- [ ] FF5+momentum 직교화
- [ ] **Realistic execution audit** (publish lag distribution + 산업 추격 alpha decay)
- [ ] Contamination audit (LLM cutoff Jan 2026 vs contract date 2008-2026 + firm-name masking)

---

## Skill Harness

- `.claude/skills/abandon-criteria/SKILL.md` v1.1
- `.claude/skills/drift-watchdog/SKILL.md`
- `.claude/skills/karpathy-guidelines/SKILL.md`
- `.claude/skills/repo-autonomy-overnight/SKILL.md`

---

## Deliverables

**공통**:
- [ ] GitHub public repo + README
- [ ] Streamlit dashboard URL
- [ ] Paper draft 8-12p (SSRN, military spending well-known + forward revenue LLM extension positioning)
- [ ] Interview demo 5분 + CV/LinkedIn 1-line

**close 경로별** (`d:/vscode/meta-harness/reports/`):
- Success → `{{YYYY-MM-DD}}-usaspending-contract-paper-practical.md`. Paper structure: §3 main effect + §4 robustness (cohort heterogeneity + industry-absorption mechanism + cross-LLM + contamination + masking). Reframing 2026-04-27: 산업 lead time finding 은 §4 robustness section 의 *positive identification result* 으로 흡수 (Cotropia 2017 USPTO 패턴 동형). Heterogeneity = mechanism 식별 강화, freeze 아님.
- Mechanical kill (trigger #1 ALL-3 AND fail) → `{{YYYY-MM-DD}}-usaspending-contract-postmortem.md`. main effect 자체 null 시만 발화 — paper headline 없음.

---

## 핵심 차별화

- vs **β2 (frozen)**: event-driven 동일 단 source SEC 8-K vs USAspending API. M1 = β2 의 자연 swap 후속 (PURE daemon-free)
- vs **F1**: event biotech vs event defense/IT — sector orthogonal
- vs **C2**: cross-section R&D-intensive 동일 sector 단 mechanism 다름 (USPTO patent moat vs USAspending revenue commitment) — mailbox orthogonality test
- vs **Z (closed)**: event-driven 단 daemon-free
- vs **disclosure_decay** (advisor): direct alpha vs meta-tool
