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
        risk_amount = int(deposit_amount * 0.10)
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
    model=MODEL_PRO,
    instruction=analyzer_instruction,
    tools=[get_standard_contract, calculate_risk_amount],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=10000),
        response_mime_type="application/json",
    ),
    output_key="risk_analysis",
)

# ---------------------------------------------------------------------------
# Agent 3: CognitiveTranslator
# ---------------------------------------------------------------------------
def translator_instruction(context):
    """Agent 3 instruction — 위험 분석 결과를 쉬운 한국어로 변환."""
    risk = context.state.get("risk_analysis", "{}")
    return f"""당신은 법률 용어를 쉬운 한국어로 변환하는 전문가입니다.
아래 위험 분석 결과의 각 위험 조항에 대해 3단계 쉬운 한국어 설명을 생성하세요.

위험 분석 결과:
{risk}

반드시 아래 JSON 형식으로 출력하세요:
{{
  "translations": [
    {{
      "number": "제N조",
      "title": "조항 제목",
      "easyKorean": {{
        "level1": "쉬운 설명 — 핵심만 1-2문장으로. 주어+서술어 명확히.",
        "level2": "비유 설명 — 일상생활 비유로 설명. '~와 같습니다' 형태.",
        "level3": "구체적 시나리오 — 실제 금액과 상황을 넣어 시나리오로 설명."
      }}
    }}
  ]
}}

변환 규칙:
- level1: 핵심을 1-2문장으로. 법률 용어 없이. "~합니다/~없습니다" 체.
- level2: 일상생활 비유. "~와 같습니다" 형태.
- level3: 구체적 금액/기간/상황을 넣은 시나리오.
- 농인/난청인이 이해할 수 있는 명확한 주어-서술어 구조 사용.
- JSON만 출력하세요."""


translator_agent = Agent(
    name="cognitive_translator",
    model=MODEL_FLASH,
    instruction=translator_instruction,
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,
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
      "status": "safe" 또는 "caution"
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
- JSON만 출력하세요."""


action_agent = Agent(
    name="action_generator",
    model=MODEL_FLASH,
    instruction=action_instruction,
    tools=[route_action],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.5,
        response_mime_type="application/json",
    ),
    output_key="final_result",
)

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
pipeline = SequentialAgent(
    name="clearsign_pipeline",
    sub_agents=[parser_agent, analyzer_agent, translator_agent, action_agent],
)
