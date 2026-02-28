"""ClearSign ADK 3-Agent Pipeline — 임대차 계약서 위험 분석 (최적화)"""

import json
import os

from google.adk.agents import Agent, SequentialAgent
from google.genai import types

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STANDARD_CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "data", "standard_contract.json")

MODEL_FLASH = "gemini-3-flash-preview"

# Pre-load standard contract at module level (avoids tool call overhead)
with open(STANDARD_CONTRACT_PATH, "r", encoding="utf-8") as _f:
    STANDARD_CONTRACT_TEXT = json.dumps(json.load(_f), ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# Agent 1: DocumentParser (unchanged)
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
# Agent 2: RiskAnalyzer (tools removed → prompt inline + JSON mode)
# ---------------------------------------------------------------------------
def analyzer_instruction(context):
    """Agent 2 instruction — 표준 계약서와 위험 금액 산출 기준을 프롬프트에 직접 삽입."""
    parsed = context.state.get("parsed_document", "{}")
    return f"""당신은 임대차 계약서 위험 분석 전문가입니다.
아래 파싱된 계약서를 국토교통부 표준 계약서와 비교하여 위험 조항을 분석하세요.

## 국토교통부 표준 주택임대차계약서 (비교 기준)

{STANDARD_CONTRACT_TEXT}

## 파싱된 계약서

{parsed}

## 위험 금액 직접 계산 기준

파싱된 계약서의 보증금(deposit_amount)과 월세(monthly_rent)를 사용하여 계산하세요:
- 이탈도 90 이상: 보증금 × 20%
- 이탈도 80~89: 보증금 × 10%
- 이탈도 70~79: 보증금 × 15%
- 이탈도 60~69: 월세 × 12개월
- 이탈도 40~59: 월세 × 6개월
- 이탈도 0~39: 월세 × 3개월

## 출력 JSON 형식

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

## 분석 기준
- deviationScore 0-20: safe (표준과 거의 동일)
- deviationScore 21-40: caution (경미한 이탈)
- deviationScore 41-60: warning (주의 필요)
- deviationScore 61-100: danger (심각한 이탈)
- 임차인에게 불리한 방향의 변경만 위험으로 판정
- deviationScore 41 이상인 조항만 deviated_clauses에 포함
- JSON만 출력하세요."""


analyzer_agent = Agent(
    name="risk_analyzer",
    model=MODEL_FLASH,
    instruction=analyzer_instruction,
    # tools 제거 → 프롬프트에 인라인, response_mime_type 사용 가능
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    ),
    output_key="risk_analysis",
)

# ---------------------------------------------------------------------------
# Agent 3: UnifiedTranslatorAction (Agent 3+4 병합)
# ---------------------------------------------------------------------------
def unified_instruction(context):
    """Agent 3 instruction — 인지적 변환 + 행동 스크립트 + 최종 JSON 생성을 통합."""
    risk = context.state.get("risk_analysis", "{}")
    parsed = context.state.get("parsed_document", "{}")
    return f"""위험 분석 결과를 바탕으로 쉬운 한국어 변환 + 행동 스크립트 + 최종 보고서를 생성하세요.

## 7대 변환 원칙 (간략)
1. 복합문→단문, 수동→능동 ("보증금이 반환된다"→"집주인이 보증금을 돌려줍니다")
2. 조사 의존 감소: "누가/무엇을/누구에게" 명시 분리
3. 중첩 조건→번호 매긴 개별 조건+결과 쌍
4. 시간 전치: 기한을 문장 맨 앞 배치
5. 한자어→일상어 (원상회복→처음 상태로 고치기, 대항력→권리 주장 힘, 전대→다시 빌려주기, 채무불이행→약속 안 지키기, 해지→계약 끝내기, 위약금→벌금, 갱신→연장, 임차인→세입자, 임대인→집주인)
6. 모든 문장에 명시적 주어 포함
7. "누가|무엇을|언제|결과" 구조화

## 행동 유형
- deviationScore>60 → type:"danger", priority:"urgent"
- deviationScore<=60 → type:"negotiate", priority:"high"

## 입력
위험 분석: {risk}
파싱 원본: {parsed}

## 출력 JSON
{{
  "summary": {{"totalMaxRisk":합계,"riskLevel":"high/medium/low","deviatedClauseCount":N,"totalClauseCount":N,"riskGrade":"위험/주의/안전","headline":"이 계약서에서 잃을 수 있는 최대 금액"}},
  "clauses": [
    {{"number":"제N조","title":"제목","deviationScore":N,"riskAmount":N,"direction":"이탈요약","original":"원문","standard":"표준원문",
      "easyKorean":{{"level1":"핵심 1-2문장(7원칙적용)","level2":"일상비유","level3":"구체적 금액/상황 시나리오"}},
      "structuredBreakdown":{{"who":"주체","what":"내용","when":"시기","condition":"조건","result":"결과","risk":"위험"}},
      "termGlossary":[{{"original":"용어","simple":"설명","context":"의미"}}],
      "action":{{"type":"danger/negotiate","priority":"urgent/high","message":"행동스크립트"}}
    }}
  ],
  "safeClausesSummary": [{{"number":"제N조","title":"제목","deviationScore":N,"status":"safe/caution","body":"원문"}}],
  "overallAction": {{"type":"warning","message":"위험조항수+최대손실+체크리스트"}}
}}

## 규칙
- level1: 법률용어 0개, ~합니다 체, 1문장 1아이디어
- level2: "~와 같습니다" 비유
- level3: 실제 금액/기간 포함 시나리오
- action.message: danger는 "⚠️"+수정요청, negotiate는 "📋 수정 요청:"+근거법. 존댓말.
- termGlossary: 조항당 2개+
- JSON만 출력."""


unified_agent = Agent(
    name="unified_translator_action",
    model=MODEL_FLASH,
    instruction=unified_instruction,
    # tools 없음 → response_mime_type 사용 가능
    generate_content_config=types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type="application/json",
    ),
    output_key="final_result",
)

# ---------------------------------------------------------------------------
# Pipeline (3-agent: Parser → Analyzer → UnifiedTranslatorAction)
# ---------------------------------------------------------------------------
pipeline = SequentialAgent(
    name="clearsign_pipeline",
    sub_agents=[parser_agent, analyzer_agent, unified_agent],
)
