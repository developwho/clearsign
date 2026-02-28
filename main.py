"""ClearSign — FastAPI Backend with ADK Pipeline + Fallback Chain"""

import asyncio
import json
import logging
import os
import traceback

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clearsign")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PORT = int(os.environ.get("PORT", 8080))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "시연, 문제정의 시작 화면")
FALLBACK_PATH = os.path.join(DATA_DIR, "fallback_analysis.json")
TIMEOUT_SECONDS = 25

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="ClearSign", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_fallback() -> dict:
    """Load pre-built fallback analysis JSON."""
    with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_output(data: dict) -> bool:
    """Validate that output matches the frontend-expected schema."""
    if not isinstance(data, dict):
        return False
    if "summary" not in data or "clauses" not in data:
        return False
    summary = data["summary"]
    if not all(k in summary for k in ("totalMaxRisk", "riskLevel", "deviatedClauseCount", "totalClauseCount")):
        return False
    for clause in data["clauses"]:
        if not all(k in clause for k in ("number", "title", "deviationScore", "riskAmount", "original", "standard")):
            return False
        if "easyKorean" not in clause:
            return False
        ek = clause["easyKorean"]
        if not all(k in ek for k in ("level1", "level2", "level3")):
            return False
        if "action" not in clause:
            return False
        act = clause["action"]
        if not all(k in act for k in ("type", "priority", "message")):
            return False
    if "overallAction" not in data:
        return False
    return True


def ensure_risk_amounts(data: dict) -> dict:
    """Fill missing riskAmount defaults and recalculate totalMaxRisk."""
    total = 0
    for clause in data.get("clauses", []):
        if "riskAmount" not in clause or not isinstance(clause["riskAmount"], (int, float)):
            clause["riskAmount"] = 1000000
        total += clause["riskAmount"]
    if "summary" in data:
        data["summary"]["totalMaxRisk"] = total
    return data


# ---------------------------------------------------------------------------
# ADK Pipeline Runner (Attempt 1)
# ---------------------------------------------------------------------------

async def run_adk_pipeline(file_bytes: bytes, mime_type: str) -> dict | None:
    """Run the ADK 4-agent pipeline. Returns parsed JSON or None on failure."""
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        from agents import pipeline

        session_service = InMemorySessionService()
        runner = Runner(
            agent=pipeline,
            app_name="clearsign",
            session_service=session_service,
        )

        session = await session_service.create_session(
            app_name="clearsign",
            user_id="user_1",
        )

        user_content = types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                types.Part.from_text(text="이 임대차 계약서를 분석해주세요. 모든 조항을 추출하고, 표준 계약서와 비교하여 위험 조항을 찾고, 쉬운 한국어로 변환하고, 행동 스크립트를 생성하세요."),
            ],
        )

        result_text = None
        async for event in runner.run_async(
            user_id="user_1",
            session_id=session.id,
            new_message=user_content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                result_text = event.content.parts[0].text
                break

        # If no final response text, try session state
        if not result_text:
            session = await session_service.get_session(
                app_name="clearsign",
                user_id="user_1",
                session_id=session.id,
            )
            state_result = session.state.get("final_result")
            if state_result:
                result_text = state_result if isinstance(state_result, str) else json.dumps(state_result)

        if not result_text:
            logger.warning("ADK pipeline returned no result")
            return None

        data = json.loads(result_text)
        data = ensure_risk_amounts(data)

        if not validate_output(data):
            logger.warning("ADK output failed schema validation")
            return None

        logger.info("ADK pipeline succeeded")
        return data

    except Exception as e:
        logger.error(f"ADK pipeline error: {e}\n{traceback.format_exc()}")
        return None


# ---------------------------------------------------------------------------
# Single Gemini Call (Attempt 2)
# ---------------------------------------------------------------------------

SINGLE_CALL_PROMPT = """당신은 임대차 계약서 위험 분석 AI입니다.
업로드된 계약서를 분석하여 아래 JSON 형식으로 결과를 출력하세요.

분석 과정:
1. 계약서에서 모든 조항을 추출합니다.
2. 국토교통부 표준 주택임대차계약서와 비교합니다.
3. 표준 대비 임차인에게 불리하게 변경된 조항을 찾습니다.
4. 각 위험 조항에 대해 쉬운 한국어 3단계 설명과 행동 스크립트를 생성합니다.

표준 계약서 핵심 조항:
- 제4조: 보증금은 기간 만료/해지 후 1개월 이내 반환
- 제7조: 쌍방 해지권, 6-2개월 전 통지, 3기분 연체 시 임대인 해지
- 제8조: 주요 설비 수선은 임대인, 소모품만 임차인
- 제9조: 위약금 보증금의 10%, 쌍방 동일 적용
- 제10조: 특약은 관계 법령 범위 내

출력 JSON 스키마:
{
  "summary": {
    "totalMaxRisk": 위험금액합계(숫자),
    "riskLevel": "high" 또는 "medium" 또는 "low",
    "deviatedClauseCount": 위험조항수(숫자),
    "totalClauseCount": 전체조항수(숫자),
    "riskGrade": "위험" 또는 "주의" 또는 "안전",
    "headline": "이 계약서에서 잃을 수 있는 최대 금액"
  },
  "clauses": [
    {
      "number": "제N조",
      "title": "조항 제목",
      "deviationScore": 0-100,
      "riskAmount": 위험금액(숫자),
      "direction": "이탈 방향 1줄 요약",
      "original": "이 계약서 원문",
      "standard": "표준 계약서 원문",
      "easyKorean": {
        "level1": "쉬운 설명 (핵심 1-2문장)",
        "level2": "비유 설명 (일상 비유)",
        "level3": "구체적 시나리오 (금액/상황 포함)"
      },
      "action": {
        "type": "danger" 또는 "negotiate",
        "priority": "urgent" 또는 "high",
        "message": "행동 스크립트 (수정 요청 문구 포함)"
      }
    }
  ],
  "safeClausesSummary": [
    {
      "number": "제N조",
      "title": "조항 제목",
      "deviationScore": 0-40,
      "status": "safe" 또는 "caution"
    }
  ],
  "overallAction": {
    "type": "warning",
    "message": "전체 경고 메시지"
  }
}

JSON만 출력하세요."""


async def run_single_gemini(file_bytes: bytes, mime_type: str) -> dict | None:
    """Fallback: single Gemini call with full prompt."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-pro",
            contents=types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    types.Part.from_text(text=SINGLE_CALL_PROMPT),
                ],
            ),
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )

        result_text = response.text
        if not result_text:
            logger.warning("Single Gemini call returned empty")
            return None

        data = json.loads(result_text)
        data = ensure_risk_amounts(data)

        if not validate_output(data):
            logger.warning("Single Gemini output failed validation")
            return None

        logger.info("Single Gemini call succeeded")
        return data

    except Exception as e:
        logger.error(f"Single Gemini error: {e}\n{traceback.format_exc()}")
        return None


# ---------------------------------------------------------------------------
# Fraud Check — Search Grounding (F6)
# ---------------------------------------------------------------------------

async def search_lease_fraud(address: str) -> dict:
    """Google Search Grounding으로 전세사기 관련 정보를 검색합니다."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""다음 주소 주변의 전세사기, 보증금 미반환, 임대차 분쟁 관련 최신 뉴스와 정보를 검색하세요.

주소: {address}

검색할 내용:
1. 해당 지역 전세사기 피해 사례
2. 보증금 미반환 사건
3. 임대인 관련 분쟁 이력
4. 해당 지역 부동산 사기 주의보

검색 결과를 바탕으로 해당 지역의 전세 거래 안전도를 평가하고,
주의해야 할 사항을 알려주세요."""

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )

        result_text = response.text or ""

        # Extract grounding sources
        sources = []
        for candidate in response.candidates:
            gm = candidate.grounding_metadata
            if gm and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if chunk.web:
                        sources.append({
                            "title": chunk.web.title or "",
                            "url": chunk.web.uri or "",
                        })

        return {
            "searchPerformed": True,
            "address": address,
            "summary": result_text,
            "sources": sources,
            "manualCheckLinks": _get_manual_links(),
        }

    except Exception as e:
        logger.error(f"Search grounding error: {e}")
        return _get_fraud_fallback(address)


def _get_manual_links() -> list:
    return [
        {"name": "인터넷등기소", "url": "https://www.iros.go.kr"},
        {"name": "실거래가 공개시스템", "url": "https://rt.molit.go.kr"},
        {"name": "HUG 전세보증금보증", "url": "https://www.khug.or.kr"},
        {"name": "대한법률구조공단", "url": "https://www.klac.or.kr", "phone": "132"},
    ]


def _get_fraud_fallback(address: str) -> dict:
    return {
        "searchPerformed": False,
        "address": address,
        "summary": "검색을 수행할 수 없습니다. 아래 링크에서 직접 확인해주세요.",
        "sources": [],
        "manualCheckLinks": _get_manual_links(),
    }


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "api_key_set": bool(GEMINI_API_KEY)}


@app.get("/api/demo")
async def demo():
    """Return pre-built fallback analysis for demo."""
    return JSONResponse(content=load_fallback())


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """Upload contract file → ADK pipeline → fallback chain → JSON response."""
    file_bytes = await file.read()
    mime_type = file.content_type or "application/pdf"

    # Normalize mime types
    if mime_type == "application/octet-stream":
        ext = (file.filename or "").lower()
        if ext.endswith(".pdf"):
            mime_type = "application/pdf"
        elif ext.endswith((".png",)):
            mime_type = "image/png"
        elif ext.endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"

    logger.info(f"Analyzing file: {file.filename} ({mime_type}, {len(file_bytes)} bytes)")

    # Attempt 1: ADK Pipeline (25s timeout)
    try:
        result = await asyncio.wait_for(
            run_adk_pipeline(file_bytes, mime_type),
            timeout=TIMEOUT_SECONDS,
        )
        if result:
            return JSONResponse(content=result)
    except asyncio.TimeoutError:
        logger.warning("ADK pipeline timed out")
    except Exception as e:
        logger.error(f"ADK attempt failed: {e}")

    # Attempt 2: Single Gemini call (25s timeout)
    try:
        result = await asyncio.wait_for(
            run_single_gemini(file_bytes, mime_type),
            timeout=TIMEOUT_SECONDS,
        )
        if result:
            return JSONResponse(content=result)
    except asyncio.TimeoutError:
        logger.warning("Single Gemini timed out")
    except Exception as e:
        logger.error(f"Single Gemini attempt failed: {e}")

    # Attempt 3: Static fallback (always succeeds)
    logger.info("Returning static fallback")
    return JSONResponse(content=load_fallback())


@app.get("/api/fraud-check")
async def fraud_check(address: str = ""):
    """Google Search Grounding for lease fraud detection (F6)."""
    if not address:
        return JSONResponse(
            status_code=400,
            content={"error": "address parameter required"},
        )
    result = await search_lease_fraud(address)
    return JSONResponse(content=result)


@app.get("/static/fallback.json")
async def static_fallback():
    """Frontend triple-fallback: serve fallback JSON as static file."""
    return FileResponse(FALLBACK_PATH, media_type="application/json")


# ---------------------------------------------------------------------------
# SPA & Static Files
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Serve frontend SPA."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path, media_type="text/html")


# Mount static directory for any additional assets
if os.path.isdir(STATIC_DIR):
    app.mount("/static-assets", StaticFiles(directory=STATIC_DIR), name="static-assets")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
