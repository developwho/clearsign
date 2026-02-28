"""ClearSign ADK 4-Agent Pipeline — 임대차 계약서 위험 분석"""

import json
import os

from google.adk.agents import Agent, SequentialAgent
from google.genai import types

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STANDARD_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "data", "standard_contract.json")

MODEL_FLASH = "gemini-3-flash-preview"
MODEL_PRO = "gemini-3.1-pro-preview"

# ---------------------------------------------------------------------------
# Tool Functions (docstring 필수 — 없으면 ADK 등록 실패)
# ---------------------------------------------------------------------------

def get_standard_contract() -> dict:
    """국토교통부 표준 주택임대차계약서를 조회합니다.

    Returns:
        dict: 표준 계약서 전체 내용 (조항별 body, key_protection, legal_basis 포함)
    """
    with open(STANDARD_CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_risk_amount(
    clause_number: str,
    deviation_score: int,
    deposit_amount: int = 50000000,
    monthly_rent: int = 500000,
) -> dict:
    """이탈도를 기반으로 해당 조항의 위험 금액을 산출합니다.

    Args:
        clause_number: 조항 번호 (예: "제4조")
        deviation_score: 표준 대비 이탈 점수 (0-100)
        deposit_amount: 보증금 금액 (기본 5000만원)
        monthly_rent: 월세 금액 (기본 50만원)

    Returns:
        dict: clause_number, deviation_score, risk_amount, calculation_basis
    """
    if deviation_score >= 90:
        risk_amount = int(deposit_amount * 0.20)
    elif deviation_score >= 80:
        risk_amount = int(deposit_amount * 0.10)
    elif deviation_score >= 70:
        risk_amount = int(deposit_amount * 0.15)
    elif deviation_score >= 60:
        risk_amount = int(monthly_rent * 12)
    elif deviation_score >= 40:
        risk_amount = int(monthly_rent * 6)
    else:
        risk_amount = int(monthly_rent * 3)

    return {
        "clause_number": clause_number,
        "deviation_score": deviation_score,
        "risk_amount": risk_amount,
        "calculation_basis": f"보증금 {deposit_amount:,}원, 월세 {monthly_rent:,}원 기준",
    }


def generate_cloze_scoring_rubric(
    clause_number: str,
    target_term: str,
    correct_answer: str,
) -> dict:
    """Cloze 문항의 의미 기반 유연 채점 기준을 생성합니다.

    농인/난청인의 철자·조사 오류를 허용하는 채점 기준을 만듭니다.

    Args:
        clause_number: 조항 번호 (예: "제4조")
        target_term: 빈칸에 들어갈 핵심 개념어
        correct_answer: 정답

    Returns:
        dict: clause_number, target_term, correct_answer, acceptable_synonyms, scoring_note
    """
    return {
        "clause_number": clause_number,
        "target_term": target_term,
        "correct_answer": correct_answer,
        "acceptable_synonyms": [correct_answer],
        "scoring_note": "철자 오류, 조사 차이, 동의어 사용 모두 정답 처리. 의미 일치 여부만 판단.",
    }


def route_action(deviation_score: int) -> dict:
    """이탈 점수에 따라 행동 유형과 우선순위를 결정합니다.

    Args:
        deviation_score: 표준 대비 이탈 점수 (0-100)

    Returns:
        dict: type(danger/negotiate), priority(urgent/high/medium), guidance
    """
    if deviation_score > 60:
        return {
            "type": "danger",
            "priority": "urgent",
            "guidance": "즉시 수정 요청 필요. 표준 계약서 기준으로 변경을 요구하세요.",
        }
    else:
        return {
            "type": "negotiate",
            "priority": "high",
            "guidance": "협상을 통해 수정 가능. 표준 계약서 조항을 근거로 제시하세요.",
        }


# ---------------------------------------------------------------------------
# Agent 1: DocumentParser
# ---------------------------------------------------------------------------
PARSER_INSTRUCTION = """당신은 임대차 계약서 파싱 전문가입니다.
업로드된 계약서(PDF 또는 이미지)에서 모든 조항을 추출하세요.

반드시 아래 JSON 형식으로 출력하세요:
{
  "title": "계약서 제목",
  "deposit_amount": 보증금(숫자),
  "monthly_rent": 월세(숫자),
  "clauses": [
    {
      "number": "제N조",
      "title": "조항 제목",
      "body": "조항 전문"
    }
  ]
}

주의사항:
- 모든 조항을 빠짐없이 추출하세요.
- 특약사항도 반드시 포함하세요.
- body에는 원문 그대로 기재하세요.
- 보증금/월세 금액이 명시되지 않으면 기본값 50000000/500000을 사용하세요.
- JSON만 출력하세요. 다른 텍스트는 포함하지 마세요."""

parser_agent = Agent(
    name="document_parser",
    model=MODEL_FLASH,
    instruction=PARSER_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json",
    ),
    output_key="parsed_document",
)

# ---------------------------------------------------------------------------
# Agent 2: RiskAnalyzer
# ---------------------------------------------------------------------------
def analyzer_instruction(context):
    """Agent 2 instruction — state에서 파싱 결과를 읽어 프롬프트에 주입."""
    parsed = context.state.get("parsed_document", "{}")
    return f"""당신은 임대차 계약서 위험 분석 전문가입니다.
아래 파싱된 계약서를 국토교통부 표준 계약서와 비교하여 위험 조항을 분석하세요.

반드시 get_standard_contract 도구를 호출하여 표준 계약서를 조회한 후 비교하세요.
각 위험 조항에 대해 calculate_risk_amount 도구를 호출하여 위험 금액을 산출하세요.

파싱된 계약서:
{parsed}

반드시 아래 JSON 형식으로 출력하세요:
{{
  "deviated_clauses": [
    {{
      "number": "제N조",
      "title": "조항 제목",
      "deviationScore": 0-100 (표준 대비 이탈 정도),
      "riskAmount": 위험금액(숫자),
      "direction": "이탈 방향 요약 (1줄)",
      "original": "이 계약서의 해당 조항 원문",
      "standard": "표준 계약서의 해당 조항 원문"
    }}
  ],
  "safe_clauses": [
    {{
      "number": "제N조",
      "title": "조항 제목",
      "deviationScore": 0-40,
      "status": "safe" 또는 "caution"
    }}
  ],
  "deposit_amount": 보증금,
  "monthly_rent": 월세
}}

분석 기준:
- deviationScore 0-20: safe (표준과 거의 동일)
- deviationScore 21-40: caution (경미한 이탈)
- deviationScore 41-60: warning (주의 필요)
- deviationScore 61-100: danger (심각한 이탈)
- 임차인에게 불리한 방향의 변경만 위험으로 판정
- deviationScore 41 이상인 조항만 deviated_clauses에 포함
- JSON만 출력하세요."""


analyzer_agent = Agent(
    name="risk_analyzer",
    model=MODEL_FLASH,  # pro는 tools+async에서 타임아웃 발생
    instruction=analyzer_instruction,
    tools=[get_standard_contract, calculate_risk_amount],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        # response_mime_type은 tools와 함께 사용 불가 (ADK 제약)
    ),
    output_key="risk_analysis",
)

# ---------------------------------------------------------------------------
# Agent 3: CognitiveTranslator
# ---------------------------------------------------------------------------
def translator_instruction(context):
    """Agent 3 instruction — 연구 기반 인지적 변환으로 쉬운 한국어 생성."""
    risk = context.state.get("risk_analysis", "{}")
    parsed = context.state.get("parsed_document", "{}")
    return f"""당신은 농인·난청인을 위한 법률 문서 인지적 변환 전문가입니다.
아래 위험 분석 결과의 각 위험 조항에 대해 3단계 쉬운 한국어 설명을 생성하세요.

## 배경: KSL(한국수어)과 한국어의 언어학적 차이
- KSL은 독립 언어로, 한국어와 문법 구조가 다릅니다.
- KSL 화자는 시공간적 스케치패드(visuospatial sketchpad)를 주된 인지 처리 경로로 사용합니다.
- 음운 루프(phonological loop) 기반의 가독성 지표(KRI 등)는 농인에게 타당하지 않습니다.
- 따라서 "읽기 쉬운 글"이 아니라 "인지적으로 접근 가능한 글"을 만들어야 합니다.

## 7대 변환 원칙 (ISO 24495-1 Plain Language + KSL 언어학 + Leichte Sprache)

### 원칙 1: 통사 구조 재배열
- 복합문 → 1문장 1아이디어 단문으로 분해
- 수동태 → 능동태 전환 (Leichte Sprache 원칙)
- 예: "보증금이 반환된다" → "집주인이 보증금을 돌려줍니다"

### 원칙 2: 조사 의존도 감소
- 격조사만으로 역할을 표현하지 말 것
- "누가 / 무엇을 / 누구에게" 를 명시적으로 분리
- KSL은 어순+공간으로 격을 실현하므로, 조사에 의존한 문장은 오해 위험

### 원칙 3: 조건/예외 분해
- 중첩 조건문 → 번호 매긴 개별 조건으로 분리
- 각 조건 직후에 결과를 배치 (조건→결과 쌍)
- 예: "다만 ~한 경우에는 ~하되 ~일 때는" → "1. ~하면 → ~합니다. 2. ~하면 → ~합니다."

### 원칙 4: 시간 전치
- 기한/시기를 문장 맨 앞에 배치
- KSL의 시간 부사 전치 전략과 일치
- 예: "보증금을 1개월 이내에 반환한다" → "1개월 안에, 집주인이 보증금을 돌려줍니다"

### 원칙 5: 한자어 법률 용어 분해
- 모든 법률 한자어를 일상어로 풀어쓰기
- 용어 사전:
  · 원상회복 → 집을 처음 상태로 고치는 것
  · 대항력 → 새 집주인에게도 내 권리를 주장할 수 있는 힘
  · 전대 → 다른 사람에게 다시 빌려주는 것
  · 채무불이행 → 약속을 지키지 않는 것
  · 하자 → 고장이나 문제
  · 면책 → 책임을 지지 않는 것
  · 해지 → 계약을 끝내는 것
  · 위약금 → 약속을 어기면 내는 벌금
  · 갱신 → 계약을 다시 연장하는 것
  · 임차인 → 세입자 (집을 빌린 사람)
  · 임대인 → 집주인 (집을 빌려준 사람)

### 원칙 6: 행위자 중심 서술
- 모든 문장에 명시적 주어를 포함
- 생략된 주어를 복원 (한국어의 주어 생략 → 농인에게 혼란)
- 예: "반환하여야 한다" → "집주인이 돌려주어야 합니다"

### 원칙 7: 공간적 정보 구조화
- "누가 | 무엇을 | 언제 | 결과" 형태로 구조화
- KSL의 시공간적 정보 배치와 일치
- structuredBreakdown 필드에 반영

## 입력 데이터

위험 분석 결과:
{risk}

파싱된 원본 계약서 (금액/기간 참조용):
{parsed}

## 출력 JSON 형식

반드시 아래 JSON 형식으로 출력하세요:
{{
  "translations": [
    {{
      "number": "제N조",
      "title": "조항 제목",
      "easyKorean": {{
        "level1": "쉬운 설명 — 핵심만 1-2문장. 7대 원칙 모두 적용.",
        "level2": "비유 설명 — 일상생활 비유로 설명. '~와 같습니다' 형태.",
        "level3": "구체적 시나리오 — 실제 금액과 상황을 넣어 시나리오로 설명."
      }},
      "structuredBreakdown": {{
        "who": "행위 주체 (예: 집주인, 세입자)",
        "what": "행위 내용 (예: 보증금을 돌려줍니다)",
        "when": "시기/기한 (예: 계약 끝난 뒤 1개월 안에)",
        "condition": "조건 (예: 새 세입자가 들어오면)",
        "result": "결과 (예: 보증금을 받을 수 있습니다)",
        "risk": "위험 (예: 기한이 없어서 오래 기다릴 수 있습니다)"
      }},
      "termGlossary": [
        {{
          "original": "원래 법률 용어",
          "simple": "쉬운 설명",
          "context": "이 조항에서의 의미"
        }}
      ]
    }}
  ]
}}

## 변환 규칙 요약
- level1: 원칙 1~7 모두 적용. 법률 용어 0개. "~합니다/~없습니다" 체. 1문장 1아이디어.
- level2: 일상생활 비유. "~와 같습니다" 형태.
- level3: 구체적 금액/기간/상황을 넣은 시나리오. 파싱된 계약서의 실제 금액 사용.
- structuredBreakdown: 모든 필드 필수. 해당 없으면 "없음".
- termGlossary: 해당 조항에 등장하는 법률 용어 최소 2개 이상.
- JSON만 출력하세요."""


translator_agent = Agent(
    name="cognitive_translator",
    model=MODEL_FLASH,
    instruction=translator_instruction,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type="application/json",
    ),
    output_key="translated_result",
)

# ---------------------------------------------------------------------------
# Agent 4: ActionGenerator
# ---------------------------------------------------------------------------
def action_instruction(context):
    """Agent 4 instruction — 행동 스크립트 생성 + 최종 JSON 조합."""
    risk = context.state.get("risk_analysis", "{}")
    translated = context.state.get("translated_result", "{}")
    return f"""당신은 임차인 보호를 위한 행동 스크립트 생성 전문가입니다.
위험 분석과 쉬운 한국어 변환 결과를 조합하여 최종 분석 보고서를 생성하세요.

각 위험 조항에 대해 route_action 도구를 호출하여 행동 유형을 결정하세요.

위험 분석 결과:
{risk}

쉬운 한국어 변환 결과:
{translated}

반드시 아래 JSON 형식으로 최종 결과를 출력하세요:
{{
  "summary": {{
    "totalMaxRisk": 모든 위험 조항 riskAmount 합계,
    "riskLevel": "high"(61+이탈 조항 3+), "medium"(1-2개), "low"(없음),
    "deviatedClauseCount": 위험 조항 수,
    "totalClauseCount": 전체 조항 수,
    "riskGrade": riskLevel이 high면 "위험", medium이면 "주의", low면 "안전",
    "headline": "이 계약서에서 잃을 수 있는 최대 금액"
  }},
  "clauses": [
    {{
      "number": "제N조",
      "title": "조항 제목",
      "deviationScore": 점수,
      "riskAmount": 금액,
      "direction": "이탈 방향 요약",
      "original": "계약서 원문",
      "standard": "표준 계약서 원문",
      "easyKorean": {{
        "level1": "쉬운 설명",
        "level2": "비유 설명",
        "level3": "구체적 시나리오"
      }},
      "structuredBreakdown": {{
        "who": "행위 주체",
        "what": "행위 내용",
        "when": "시기/기한",
        "condition": "조건",
        "result": "결과",
        "risk": "위험"
      }},
      "termGlossary": [
        {{
          "original": "법률 용어",
          "simple": "쉬운 설명",
          "context": "이 조항에서의 의미"
        }}
      ],
      "action": {{
        "type": "danger" 또는 "negotiate",
        "priority": "urgent" 또는 "high",
        "message": "행동 스크립트 메시지 (수정 요청 문구 포함)"
      }}
    }}
  ],
  "safeClausesSummary": [
    {{
      "number": "제N조",
      "title": "조항 제목",
      "deviationScore": 점수,
      "status": "safe" 또는 "caution",
      "body": "조항 원문 전체 (파싱된 계약서에서 가져온 본문)"
    }}
  ],
  "overallAction": {{
    "type": "warning",
    "message": "전체 경고 메시지 (위험 조항 개수, 최대 손실 금액, 확인 사항 체크리스트 포함)"
  }}
}}

행동 스크립트 작성 규칙:
- type이 danger인 경우: "⚠️"로 시작, 위험성 설명 + 수정 요청 메시지 포함
- type이 negotiate인 경우: "📋 수정 요청 메시지:"로 시작, 근거법 언급
- 수정 요청 메시지는 존댓말로, 집주인에게 직접 말하는 형태
- overallAction.message에는 위험 조항 수, 최대 손실, 확인 체크리스트 포함

structuredBreakdown / termGlossary 매핑 규칙:
- 쉬운 한국어 변환 결과(translated_result)의 각 조항에 structuredBreakdown과 termGlossary가 있으면 그대로 매핑
- 없는 경우, 해당 조항의 easyKorean 내용을 기반으로 직접 생성
- JSON만 출력하세요."""


action_agent = Agent(
    name="action_generator",
    model=MODEL_FLASH,
    instruction=action_instruction,
    tools=[route_action],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.5,
        # response_mime_type은 tools와 함께 사용 불가 (ADK 제약)
    ),
    output_key="final_result",
)

# ---------------------------------------------------------------------------
# Agent 5: ComprehensionVerifier
# ---------------------------------------------------------------------------
def verifier_instruction(context):
    """Agent 5 instruction — ISO 24495-1 Find-Understand-Use 기반 이해도 검증 문항 생성."""
    translated = context.state.get("translated_result", "{}")
    risk = context.state.get("risk_analysis", "{}")
    final = context.state.get("final_result", "{}")
    return f"""당신은 농인·난청인 대상 문서 이해도 검증 전문가입니다.
ISO 24495-1의 Find-Understand-Use 프레임워크에 기반하여
쉬운 한국어로 변환된 계약서 설명의 이해도를 검증하는 문항을 생성하세요.

## 배경
- Cloze Test는 농인 대상 타당도/신뢰도가 검증된 이해도 측정 도구입니다.
- 채점 시 철자 오류, 조사 차이, 동의어는 모두 정답으로 처리합니다 (의미 기반 유연 채점).
- 3종 문항을 통해 Find(찾기), Understand(이해), Use(활용) 수준을 모두 평가합니다.

## 입력 데이터

쉬운 한국어 변환 결과:
{translated}

위험 분석 결과:
{risk}

최종 행동 스크립트:
{final}

## 출력 JSON 형식

generate_cloze_scoring_rubric 도구를 호출하여 각 Cloze 문항의 채점 기준을 생성하세요.

반드시 아래 JSON 형식으로 출력하세요:
{{
  "comprehension": {{
    "clozeQuestions": [
      {{
        "clauseNumber": "제N조",
        "questionType": "cloze",
        "sentence": "빈칸이 포함된 문장 (핵심 개념어를 ___로 대체)",
        "question": "빈칸에 들어갈 알맞은 말은 무엇인가요?",
        "answer": "정답",
        "acceptableSynonyms": ["동의어1", "동의어2"],
        "scoringNote": "의미 일치 여부만 판단. 철자·조사 오류 허용."
      }}
    ],
    "scenarioQuestions": [
      {{
        "clauseNumber": "제N조",
        "questionType": "scenario",
        "scenario": "구체적인 상황 설명 (일상적 맥락)",
        "question": "이런 상황에서 어떻게 해야 하나요?",
        "choices": [
          {{"label": "A", "text": "선택지 1"}},
          {{"label": "B", "text": "선택지 2"}},
          {{"label": "C", "text": "선택지 3"}}
        ],
        "correctAnswer": "A",
        "explanation": "정답 이유 설명 (쉬운 한국어로)"
      }}
    ],
    "recallQuestions": [
      {{
        "questionType": "recall",
        "question": "이 계약서에서 가장 위험한 점 3가지는 무엇인가요?",
        "goldStandardIdeas": [
          "핵심 아이디어 1",
          "핵심 아이디어 2",
          "핵심 아이디어 3"
        ],
        "scoringNote": "3가지 중 2가지 이상 언급하면 이해한 것으로 판단"
      }}
    ]
  }}
}}

## 생성 규칙
- clozeQuestions: 위험 조항별 최소 1개, 총 3~5개. level1 설명에서 핵심 개념어를 빈칸으로.
- scenarioQuestions: 위험 조항 중 상위 2~3개에 대해 "만약 ~한 상황이면?" 형태.
- recallQuestions: 전체에 대해 1개. 가장 위험한 점 3가지를 묻는 개방형.
- 모든 문장은 쉬운 한국어 (7대 변환 원칙 적용).
- JSON만 출력하세요."""


verifier_agent = Agent(
    name="comprehension_verifier",
    model=MODEL_FLASH,
    instruction=verifier_instruction,
    tools=[generate_cloze_scoring_rubric],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        # response_mime_type은 tools와 함께 사용 불가 (ADK 제약)
    ),
    output_key="verified_result",
)

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
pipeline = SequentialAgent(
    name="clearsign_pipeline",
    sub_agents=[parser_agent, analyzer_agent, translator_agent, action_agent, verifier_agent],
)
