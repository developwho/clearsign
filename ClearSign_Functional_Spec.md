# ClearSign — 핵심 기능 명세서 (Functional Spec)

> **해커톤:** Gemini 3 Seoul | 2026.02.28 | 빌드 7시간 (10:00→17:00)
> **심사 비중:** Demo 50% · Impact 25% · Creativity 15% · Pitch 10%
> **트랙:** Gemini for Good
> **한 줄 정의:** 임대차 계약서를 업로드하면 위험을 시각화하고, 이해될 때까지 설명을 바꾸며, 구체적 행동까지 생성하는 에이전틱 접근성 파이프라인

---

## 1. 사용자 시나리오 (Golden Path)

```
사용자: 임대차 계약서 PDF/사진을 업로드한다
    ↓
화면 1: 위험 지형도 — "이 계약서에서 잃을 수 있는 최대 금액: ₩24,500,000"
    ↓  (조항별 위험 비율이 시각적으로 즉시 보임)
화면 2: 조항별 Deviation Score — 표준 대비 이탈 조항이 빨간색으로 강조
    ↓  (각 조항이 "얼마나 비정상인지" 수치로 표시)
화면 3: 쉬운 한국어 변환 — 위험 조항을 쉬운 말 + 구체적 시나리오로 설명
    ↓     (structuredBreakdown + termGlossary 포함)
화면 4: 행동 스크립트 — 이탈도에 따라 협상 메시지 or 사기 경고 + 신고 연결
    ↓
화면 5: 이해도 검증 — Cloze/시나리오/회상 문항으로 계약 이해 확인
```

**데모 소요 시간 목표: PDF 업로드 → 최종 결과 30초 이내**

---

## 2. 기능 정의 (우선순위별)

### ⬛ P0: 데모 성패를 가르는 핵심 (구현 완료)

---

#### F1. 계약서 업로드 & 구조화

| 항목 | 내용 |
|---|---|
| **입력** | 임대차 계약서 PDF 또는 카메라 촬영 이미지 (최대 20MB) |
| **지원 형식** | PDF, PNG, JPG, JPEG, GIF, WEBP, BMP, TIFF, HEIC, HEIF, HTML, TXT, CSV, RTF |
| **출력** | 조항별 구조화된 JSON (조항번호, 제목, 본문 텍스트, 보증금/월세 금액) |
| **핵심 동작** | ADK Agent 1 (DocumentParser) — `gemini-3-flash-preview` 멀티모달 비전으로 문서 레이아웃 이해 → 조항 단위 파싱 |
| **성공 기준** | 국토부 표준 임대차 계약서 기준 주요 조항 10개 이상 정확 추출 |
| **폴백** | 사전 준비된 샘플 계약서의 하드코딩된 JSON으로 전환 |

**출력 스키마:**
```json
{
  "title": "계약서 제목",
  "deposit_amount": 50000000,
  "monthly_rent": 500000,
  "clauses": [
    { "number": "제N조", "title": "조항 제목", "body": "조항 전문" }
  ]
}
```

---

#### F2. Deviation Score (표준 대비 이탈도)

| 항목 | 내용 |
|---|---|
| **입력** | F1에서 추출된 조항별 JSON + 국토부 표준 계약서 baseline |
| **출력** | 조항별 이탈도 점수 (0~100%) + 이탈 방향 요약 (1문장) + 경제적 위험 금액 |
| **핵심 동작** | ADK Agent 2 (RiskAnalyzer) — `gemini-3.1-pro-preview` 의미론적 비교 수행 + 두 가지 도구 호출 |
| **도구 1** | `get_standard_contract()` — 표준 계약서 baseline 조회 |
| **도구 2** | `calculate_risk_amount(clause_number, deviation_score, deposit_amount, monthly_rent)` — 이탈도 기반 위험 금액 산출 |
| **이탈도 기준** | 0~20: safe / 21~40: caution / 41~60: warning / 61~100: danger |
| **출력 예시** | `"제8조(수리 책임) — 이탈도 87% \| 통상 임대인 책임인 부분이 임차인에게 전가됨"` |
| **성공 기준** | 위험 조항 3개 이상 정확 식별, 이탈 방향 설명이 법적으로 타당 |
| **폴백** | 핵심 5개 조항(보증금 반환, 수리 책임, 계약 해지, 특약, 위약금)만 비교 |

**위험 금액 산출 기준:**

| 이탈도 | 위험 금액 |
|---|---|
| 90% 이상 | 보증금 × 20% |
| 80~89% | 보증금 × 10% |
| 70~79% | 보증금 × 15% |
| 60~69% | 월세 × 12개월 |
| 40~59% | 월세 × 6개월 |
| ~39% | 월세 × 3개월 |

---

#### F3. 위험 지형도 시각화

| 항목 | 내용 |
|---|---|
| **입력** | F2의 이탈도 점수 + 경제적 리스크 추정 금액 |
| **출력** | 시각적 대시보드 (프론트엔드 SPA) |
| **핵심 요소** | ① 중앙 큰 숫자: "잃을 수 있는 최대 금액" ② 조항별 리스크 비율 바 차트 ③ 이탈도별 색상 코딩 (초록→노랑→빨강) |
| **summary 필드** | `totalMaxRisk`, `riskLevel`(high/medium/low), `riskGrade`(위험/주의/안전), `deviatedClauseCount`, `totalClauseCount`, `headline` |
| **성공 기준** | 텍스트를 읽지 않아도 "어디가 위험한지" 3초 안에 파악 가능 |
| **핵심 UX 원칙** | 숫자와 색상이 먼저, 텍스트는 보조. 농인/비농인 모두 동일하게 직관적 |

---

#### F4. 쉬운 한국어 변환 (인지적 접근성 변환)

> **원래 명세에서 대폭 강화:** 단순 다단계 설명 → KSL 언어학 기반 7대 원칙 적용

| 항목 | 내용 |
|---|---|
| **입력** | 이탈도 상위 위험 조항의 원문 + F2 분석 결과 |
| **핵심 동작** | ADK Agent 3 (CognitiveTranslator) — `gemini-3-flash-preview` |
| **이론적 근거** | ISO 24495-1 Plain Language + KSL 언어학 (시공간적 스케치패드) + Leichte Sprache |
| **출력** | 3단계 설명 + structuredBreakdown + termGlossary |

**3단계 설명:**

| 단계 | 내용 |
|---|---|
| **Level 1** | 쉬운 한국어 — 7대 원칙 모두 적용, 법률 용어 0개, 1문장 1아이디어 |
| **Level 2** | 시각적 비유 — "~와 같습니다" 형태의 일상 비유 |
| **Level 3** | 구체적 시나리오 — 실제 금액/기간/상황을 넣은 "만약 ~한다면" 시나리오 |

**7대 변환 원칙 (KSL 언어학 기반):**

| 원칙 | 내용 |
|---|---|
| 1. 통사 구조 재배열 | 복합문→단문, 수동태→능동태 |
| 2. 조사 의존도 감소 | "누가/무엇을/누구에게" 명시 분리 |
| 3. 조건/예외 분해 | 중첩 조건→번호 매긴 개별 조건+결과 쌍 |
| 4. 시간 전치 | 기한/시기를 문장 맨 앞 배치 |
| 5. 한자어 법률 용어 분해 | 원상회복→"집을 처음 상태로 고치는 것" 등 용어 사전 적용 |
| 6. 행위자 중심 서술 | 모든 문장에 명시적 주어 포함 |
| 7. 공간적 정보 구조화 | "누가\|무엇을\|언제\|결과" 형태 → structuredBreakdown 반영 |

**추가 출력 필드:**
- `structuredBreakdown`: who / what / when / condition / result / risk
- `termGlossary`: 조항 내 법률 용어 ≥2개, 원어/쉬운 설명/이 조항에서의 의미

**성공 기준:** 한국어가 모어가 아닌 사람(이주민/농인)이 읽어도 핵심 위험을 이해 가능

---

#### F5. 행동 스크립트 생성

| 항목 | 내용 |
|---|---|
| **입력** | F2의 이탈도 + F4의 변환 결과 |
| **핵심 동작** | ADK Agent 4 (ActionGenerator) — `gemini-3-flash-preview` + `route_action()` 도구 |
| **도구** | `route_action(deviation_score)` — 이탈도에 따라 type/priority/guidance 결정 |
| **출력 (분기)** | **이탈도 ≤ 60%:** type=`negotiate` — 표준 계약서 근거 수정 요청 메시지 |
| | **이탈도 > 60%:** type=`danger` — 전세사기 위험 경고 + 관할 주민센터/법률구조공단 연결 |
| **핵심 가치** | 농인은 전화 협상 불가 → 텍스트 기반 협상 도구가 치명적으로 필요 |
| **최종 조합** | Agent 4가 F1~F4 결과를 조합해 최종 분석 JSON (`final_result`) 생성 |

**출력 예시 (협상):**
> `"📋 수정 요청 메시지:\n집주인님, 제8조(수리 책임) 조항에 대해 말씀드립니다. 국토부 표준 계약서에 따르면 주요 시설물 수리는 임대인 책임입니다. 해당 조항을 표준에 맞게 수정해주시면 감사하겠습니다."`

**출력 예시 (경고):**
> `"⚠️ 전세사기 위험 감지 — 보증금 반환 조항 누락 + 특약에 면책 조항 존재. 계약 전 반드시 확인: ① 등기부등본 열람 ② 전입신고 ③ 법률구조공단 (132) 상담"`

---

### ⬜ P1: 임팩트를 높이는 기능 (구현 완료)

---

#### F6. 실시간 전세사기 이력 검증 (Google Search 그라운딩)

| 항목 | 내용 |
|---|---|
| **엔드포인트** | `GET /api/fraud-check?address={주소}` |
| **입력** | 계약서에서 추출된 주소 또는 임대인 정보 |
| **출력** | 검색 수행 여부 + 지역 전세사기 뉴스 요약 + 출처 URL 목록 + 공식 기관 링크 |
| **핵심 동작** | `gemini-3-flash-preview` + `google_search` 도구 (Search Grounding) |
| **수동 확인 링크** | 인터넷등기소, 실거래가 공개시스템, HUG 전세보증금보증, 대한법률구조공단(132) |
| **폴백** | 검색 실패 시 `searchPerformed: false` + 공식 기관 링크만 반환 |
| **제약** | `google_search`는 `thinking_config`, `response_mime_type="application/json"`과 동시 사용 불가 → 별도 호출로 분리 |

---

#### F7. 이해도 검증 (ISO 24495-1 기반) — 신규 추가

> **원래 명세에 없던 기능 — 개발 중 추가**

| 항목 | 내용 |
|---|---|
| **핵심 동작** | ADK Agent 5 (ComprehensionVerifier) — `gemini-3-flash-preview` |
| **이론적 근거** | ISO 24495-1 Find-Understand-Use 프레임워크 + Cloze Test (농인 대상 타당도/신뢰도 검증) |
| **도구** | `generate_cloze_scoring_rubric()` — 의미 기반 유연 채점 기준 생성 |
| **출력 문항 3종** | |
| **① Cloze 문항** | 쉬운 한국어 level1 설명에서 핵심 개념어를 `___`로 대체 (3~5개) |
| **② 시나리오 문항** | "만약 ~한 상황이면?" 상황 적용 3지선다 (위험 조항별 2~3개) |
| **③ 회상 문항** | "가장 위험한 점 3가지는?" 개방형 (전체 1개) |
| **채점 원칙** | 철자 오류, 조사 차이, 동의어 모두 정답 처리 — 의미 일치 여부만 판단 |
| **목적** | 정보가 전달된 것과 이해된 것을 구분. 농인·난청인의 실질적 계약 이해 확인 |

---

### ◻️ P2: 보너스 (시간 남으면)

---

#### F8. 관점 전환 장치 (데모 오프닝용)

| 항목 | 내용 |
|---|---|
| **설명** | 실제 계약서의 핵심 조항을 일본어 법률용어로 치환 + 어순을 뒤섞어 표시하는 별도 화면 |
| **목적** | 심사위원이 "자막이 있어도 의미가 도달하지 않는" 경험을 15초 안에 체감 |
| **구현 수준** | 프론트엔드 정적 화면 1장 (AI 불필요) |
| **데모 위치** | 1분 영상 첫 10초 / 라이브 피치 첫 15초 |

#### F9. 다국어 확장 데모

| 항목 | 내용 |
|---|---|
| **설명** | 영어 Lease Agreement를 입력해도 동일 파이프라인 작동 시연 |
| **목적** | "한국 전세 → 미국 ADA → 글로벌" 확장성 증명 |
| **폴백** | 피치에서 구두 언급만 |

---

## 3. ADK 5-Agent 파이프라인 아키텍처

> **원래 명세 대비 변경:** 4-Agent → 5-Agent (ComprehensionVerifier 추가)

```
[사용자 업로드]
      ↓
Agent 1: DocumentParser (gemini-3-flash-preview)
  - 멀티모달 비전으로 조항 파싱
  - output_key: "parsed_document"
      ↓
Agent 2: RiskAnalyzer (gemini-3.1-pro-preview)
  - 표준 계약서 비교 + 이탈도 산출
  - 도구: get_standard_contract(), calculate_risk_amount()
  - output_key: "risk_analysis"
      ↓
Agent 3: CognitiveTranslator (gemini-3-flash-preview)
  - 7대 원칙 기반 인지적 변환
  - 3단계 설명 + structuredBreakdown + termGlossary
  - output_key: "translated_result"
      ↓
Agent 4: ActionGenerator (gemini-3-flash-preview)
  - 행동 스크립트 생성 + 최종 JSON 조합
  - 도구: route_action()
  - output_key: "final_result"
      ↓
Agent 5: ComprehensionVerifier (gemini-3-flash-preview)
  - ISO 24495-1 기반 이해도 검증 문항 생성
  - 도구: generate_cloze_scoring_rubric()
  - output_key: "verified_result"
      ↓
[final_result + verified_result.comprehension 병합 → 최종 응답]
```

**에이전트 간 상태 전달:** `output_key` → 다음 에이전트 `context.state.get()`

---

## 4. Gemini 기능 매핑

| ClearSign 기능 | Gemini 기능 | 왜 Gemini 없이 불가능한가 |
|---|---|---|
| F1 (문서 구조화) | **멀티모달 비전** (`gemini-3-flash-preview`) | 스캔/사진/PDF 형태 무관하게 레이아웃 이해 + 텍스트 추출 |
| F2 (Deviation Score) | **추론** (`gemini-3.1-pro-preview`) | "동일한 의미가 다른 문장으로 표현"된 이탈을 감지하는 의미론적 비교 |
| F2 (위험 금액 산출) | **함수 호출** (Tools) | 표준계약서 baseline 조회 + 위험도 채점 함수 실행 |
| F4 (인지적 변환) | **텍스트 생성** + KSL 언어학 프롬프트 | 법률 용어 → 7대 원칙 기반 다단계 변환. 단순 사전 치환 불가 |
| F5 (행동 스크립트) | **텍스트 생성 + 함수 호출** | 이탈도 기반 조건 분기 + 맥락에 맞는 협상 메시지 생성 |
| F6 (사기 이력 검증) | **Google Search 그라운딩** | 실시간 뉴스/판례 검색으로 팩트 검증 |
| F7 (이해도 검증) | **텍스트 생성 + 함수 호출** | Cloze/시나리오/회상 문항 생성 + 의미 기반 채점 기준 생성 |
| 전체 파이프라인 | **ADK 오케스트레이션** | 5-Agent 순차 실행 + 상태 전달 |

**Gemini 기능 활용 수:** 멀티모달 비전, 추론(고성능 모델), 함수 호출, Google Search 그라운딩, ADK → **5개 이상**

---

## 5. 최종 출력 JSON 스키마

```json
{
  "summary": {
    "totalMaxRisk": 24500000,
    "riskLevel": "high",
    "riskGrade": "위험",
    "deviatedClauseCount": 5,
    "totalClauseCount": 12,
    "headline": "이 계약서에서 잃을 수 있는 최대 금액"
  },
  "clauses": [
    {
      "number": "제4조",
      "title": "보증금 반환",
      "deviationScore": 92,
      "riskAmount": 5000000,
      "direction": "이탈 방향 1줄 요약",
      "original": "계약서 원문",
      "standard": "표준 계약서 원문",
      "easyKorean": {
        "level1": "쉬운 설명 (7대 원칙 적용)",
        "level2": "비유 설명",
        "level3": "구체적 시나리오 (실제 금액 포함)"
      },
      "structuredBreakdown": {
        "who": "집주인",
        "what": "보증금을 돌려줍니다",
        "when": "정해져 있지 않음",
        "condition": "새 세입자가 들어오면",
        "result": "보증금을 받을 수 있습니다",
        "risk": "1년 넘게 못 받을 수 있습니다"
      },
      "termGlossary": [
        { "original": "면책", "simple": "책임을 지지 않는 것", "context": "..." }
      ],
      "action": {
        "type": "danger",
        "priority": "urgent",
        "message": "⚠️ 행동 스크립트"
      }
    }
  ],
  "safeClausesSummary": [
    { "number": "제N조", "title": "...", "deviationScore": 10, "status": "safe", "body": "..." }
  ],
  "overallAction": {
    "type": "warning",
    "message": "전체 경고 메시지"
  },
  "comprehension": {
    "clozeQuestions": [...],
    "scenarioQuestions": [...],
    "recallQuestions": [...]
  },
  "analysisMode": "real"
}
```

---

## 6. 데이터 요구사항

| 데이터 | 출처 | 준비 상태 | 용도 |
|---|---|---|---|
| 국토부 표준 임대차 계약서 | 국토부 공개 | `data/standard_contract.json` 완비 | F2 Deviation Score baseline |
| 샘플 위험 계약서 | 직접 제작 | `data/sample_risky_contract.json` 완비 | 데모용 입력 |
| 사전 분석 결과 (폴백) | 직접 제작 | `data/fallback_analysis.json` 완비 | 즉시 전환 데모 데이터 |
| 조항별 법적 기준 | 주택임대차보호법 | 프롬프트에 직접 임베드 | F2 판단 기준 |

---

## 7. 데모 시나리오 (1분 영상용)

### 영상 스크립트

```
[0:00-0:10] 관점 전환 장치
  화면: 일본어 법률용어로 치환된 계약서
  자막: "이것이 농인이 보는 계약서입니다. 글자는 보입니다. 의미는 도달하지 않습니다."

[0:10-0:20] 문제 선언 + 업로드
  화면: ClearSign 메인 화면 → PDF 드래그앤드롭
  자막: "ClearSign에 계약서를 올리면—"

[0:20-0:35] 핵심 데모 — 위험 지형도 + Deviation Score
  화면: 분석 로딩(2~3초) → 위험 지형도 렌더링
         중앙: "잃을 수 있는 최대 금액: ₩24,500,000"
         조항별 빨간/노란/초록 바
         이탈 조항 클릭 → Deviation Score 상세
  자막 없음 (시각적으로 자명해야 함)

[0:35-0:45] 쉬운 한국어 변환 (structuredBreakdown 포함)
  화면: 위험 조항 선택 → Level 3 시나리오 설명 표시
         "이사를 나간 뒤에도 보증금 5,000만원을 1년 넘게 못 받을 수 있습니다"
  자막: "법률 용어 없이, 실제 상황으로 설명합니다"

[0:45-0:55] 행동 스크립트
  화면: "수정 요청 메시지 생성" 버튼 → 즉시 텍스트 생성
         또는 이탈도 높을 시: "⚠️ 전세사기 위험" 경고 화면
  자막: "위험을 아는 것에서 위험을 바꾸는 것까지"

[0:55-1:00] 클로징
  화면: ClearSign 로고 + 한 문장
  자막: "정보가 전달된 것과 이해된 것은 다릅니다."
```

### 라이브 데모 (3분, Top 6 진출 시)

```
[0:00-0:30] 관점 전환 + 문제 선언 (영상 앞부분과 동일)
[0:30-2:00] 라이브 시연 — 실제 PDF 업로드 → 전체 플로우 (F7 이해도 검증 포함)
[2:00-2:30] 확장성: "농인 → 고령자 → 이주민 → 모든 사람의 계약"
[2:30-3:00] 클로징 + Q&A 대비
```

---

## 8. 폴백 계획 (3단계 체인)

| 단계 | 조건 | 동작 |
|---|---|---|
| **1차: ADK 파이프라인** | 정상 작동 | 5-Agent 순차 실행. 타임아웃 55초 |
| **2차: 단일 Gemini 호출** | ADK 실패/타임아웃 | `gemini-3-flash-preview` 단일 호출 (전체 프롬프트). 타임아웃 25초 |
| **3차: 정적 폴백** | 1, 2차 모두 실패 | `fallback_analysis.json` 즉시 반환. `analysisMode: "fallback"` 표시 |

**추가 폴백 케이스:**

| 시나리오 | 트리거 | 폴백 |
|---|---|---|
| PDF 파싱 불안정 | 멀티모달 비전 오류 | 다중 MIME 형식 지원으로 재시도 (HTML/TXT 등) |
| Google Search 그라운딩 실패 | F6 미작동 | `searchPerformed: false` + 공식 기관 링크 반환 |
| 스키마 검증 실패 | 출력 필드 누락 | `validate_output()` 실패 → 다음 폴백 단계로 강등 |
| 배포 실패 | Cloud Run 장애 | 로컬 데모 + ngrok 터널링 |
| `/api/demo` 엔드포인트 | 데모 즉시 전환 필요 | 사전 분석 결과 직접 반환 |

---

## 9. API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 상태 + API 키 설정 여부 |
| `GET` | `/api/config` | Google OAuth Client ID 반환 |
| `GET` | `/api/demo` | 사전 준비 폴백 분석 결과 반환 |
| `POST` | `/api/analyze` | 계약서 파일 업로드 → 분석 결과 반환 |
| `GET` | `/api/fraud-check?address=` | Google Search 그라운딩 전세사기 검색 |
| `GET` | `/static/fallback.json` | 프론트엔드 triple-fallback용 정적 파일 |

---

## 10. 금지사항 체크리스트 (해커톤 규정)

- [x] ~~기본 RAG~~ → 에이전틱 파이프라인 (파싱→분석→변환→행동→이해도검증)
- [x] ~~Streamlit~~ → FastAPI + 프론트엔드 SPA
- [x] ~~단순 이미지 분석~~ → 멀티홉 법률 추론 + 의미론적 비교 + KSL 언어학
- [x] ~~AI 교육 챗봇~~ → 도메인 특화 워크플로우 (임대차 계약 특화)
- [x] ~~의료 진단~~ → 법률/행정 도메인
- [x] ~~프레젠테이션~~ → "Show us what you have built" (기술 데모만)

---

*v3.0 | 구현 완료 기준 현행화 | 2026-02-28*
*변경 이력: v1.0 초안 → v2.0 심사 기준 반영 → v3.0 5-Agent 파이프라인 + ISO 24495-1 이해도 검증 + KSL 7대 원칙 반영*
