"""ClearSign — FastAPI Backend with ADK Pipeline + Fallback Chain"""

import asyncio
import json
import logging
import os
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clearsign")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY is not set — AI analysis will fall back to static data")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
SESSION_MAX_AGE_SECONDS = int(os.environ.get("SESSION_MAX_AGE_SECONDS", 7 * 24 * 60 * 60))
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").strip().lower() in ("1", "true", "yes", "on")
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "lax").strip().lower()
if COOKIE_SAMESITE not in ("lax", "strict", "none"):
    COOKIE_SAMESITE = "lax"
COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN", "").strip() or None
CORS_ORIGINS_ENV = os.environ.get("CORS_ORIGINS", "")
DEFAULT_CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",") if origin.strip()] or DEFAULT_CORS_ORIGINS
SESSION_COOKIE_NAME = "clearsign_session"
SESSION_COOKIE_SALT = "clearsign-auth-v1"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

if not GOOGLE_CLIENT_ID:
    logging.warning("GOOGLE_CLIENT_ID is not set — Google login disabled")
if not SESSION_SECRET:
    logging.warning("SESSION_SECRET is not set — Google login disabled")
PORT = int(os.environ.get("PORT", 8080))
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
FALLBACK_PATH = os.path.join(DATA_DIR, "fallback_analysis.json")
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", 180))
SINGLE_CALL_TIMEOUT = int(os.environ.get("SINGLE_CALL_TIMEOUT", 120))

# ---------------------------------------------------------------------------
# Pre-initialize ADK & Gemini (eliminate cold-start per request)
# ---------------------------------------------------------------------------
_adk_runner = None
_adk_session_service = None


def _init_adk():
    global _adk_runner, _adk_session_service
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        from agents import pipeline

        _adk_session_service = InMemorySessionService()
        _adk_runner = Runner(
            agent=pipeline,
            app_name="clearsign",
            session_service=_adk_session_service,
        )
        logger.info("ADK pipeline pre-initialized")
    except Exception as e:
        logger.warning(f"ADK pre-init failed: {e}")


_genai_client = None


def _init_genai_client():
    global _genai_client
    try:
        from google import genai

        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini client pre-initialized")
    except Exception as e:
        logger.warning(f"Gemini client pre-init failed: {e}")


if GEMINI_API_KEY:
    _init_adk()
    _init_genai_client()

# ---------------------------------------------------------------------------
# FastAPI App (with lifespan for Gemini warmup)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app):
    # Warmup: send a tiny request to prime the connection
    if GEMINI_API_KEY and _genai_client:
        try:
            from google.genai import types

            await _genai_client.aio.models.generate_content(
                model="gemini-3-flash-preview",
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=1),
            )
            logger.info("Gemini warmup completed")
        except Exception:
            logger.warning("Gemini warmup failed (non-fatal)")
    yield


app = FastAPI(title="ClearSign", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
    # comprehension is optional but if present, validate structure
    if "comprehension" in data:
        comp = data["comprehension"]
        if "clozeQuestions" in comp:
            for cq in comp["clozeQuestions"]:
                if not all(k in cq for k in ("clauseNumber", "question", "answer")):
                    return False
        if "scenarioQuestions" in comp:
            for sq in comp["scenarioQuestions"]:
                if not all(k in sq for k in ("scenario", "question", "choices")):
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


class GoogleAuthRequest(BaseModel):
    credential: str


def is_google_login_enabled() -> bool:
    return bool(GOOGLE_CLIENT_ID and SESSION_SECRET)


def _get_session_serializer():
    if not SESSION_SECRET:
        raise RuntimeError("SESSION_SECRET is not set")
    from itsdangerous import URLSafeTimedSerializer

    return URLSafeTimedSerializer(secret_key=SESSION_SECRET, salt=SESSION_COOKIE_SALT)


def _set_session_cookie(response: JSONResponse, user: dict) -> None:
    token = _get_session_serializer().dumps(user)
    cookie_params = {
        "key": SESSION_COOKIE_NAME,
        "value": token,
        "max_age": SESSION_MAX_AGE_SECONDS,
        "httponly": True,
        "secure": COOKIE_SECURE,
        "samesite": COOKIE_SAMESITE,
        "path": "/",
    }
    if COOKIE_DOMAIN:
        cookie_params["domain"] = COOKIE_DOMAIN
    response.set_cookie(**cookie_params)


def _clear_session_cookie(response: JSONResponse) -> None:
    cookie_params = {
        "key": SESSION_COOKIE_NAME,
        "path": "/",
    }
    if COOKIE_DOMAIN:
        cookie_params["domain"] = COOKIE_DOMAIN
    response.delete_cookie(**cookie_params)


def _read_session_user(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not SESSION_SECRET:
        return None

    try:
        user = _get_session_serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except Exception:
        return None

    if not isinstance(user, dict):
        return None

    user_id = user.get("id")
    email = user.get("email")
    if not user_id or not email:
        return None

    return {
        "id": str(user_id),
        "name": str(user.get("name") or ""),
        "email": str(email),
        "picture": str(user.get("picture") or ""),
    }


async def _verify_google_credential(credential: str) -> dict | None:
    if not credential or not GOOGLE_CLIENT_ID:
        return None

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
    except Exception as e:
        logger.error(f"google-auth import error: {e}")
        return None

    try:
        token_info = await asyncio.to_thread(
            id_token.verify_oauth2_token,
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as e:
        logger.warning(f"Google credential verification failed: {e}")
        return None

    issuer = token_info.get("iss")
    if issuer not in GOOGLE_ISSUERS:
        logger.warning(f"Invalid token issuer: {issuer}")
        return None

    audience = token_info.get("aud")
    if isinstance(audience, list):
        audience_ok = GOOGLE_CLIENT_ID in audience
    else:
        audience_ok = audience == GOOGLE_CLIENT_ID
    if not audience_ok:
        logger.warning("Invalid token audience")
        return None

    if not token_info.get("email_verified", False):
        logger.warning("Unverified Google account attempted login")
        return None

    user_id = token_info.get("sub")
    email = token_info.get("email")
    if not user_id or not email:
        return None

    return {
        "id": str(user_id),
        "name": str(token_info.get("name") or ""),
        "email": str(email),
        "picture": str(token_info.get("picture") or ""),
    }


# ---------------------------------------------------------------------------
# ADK Pipeline Runner (Attempt 1)
# ---------------------------------------------------------------------------

async def run_adk_pipeline(file_bytes: bytes, mime_type: str) -> dict | None:
    """Run the ADK 3-agent pipeline. Returns parsed JSON or None on failure."""
    global _adk_runner, _adk_session_service
    try:
        from google.genai import types

        if _adk_runner is None:
            _init_adk()
        if _adk_runner is None:
            return None

        user_id = str(uuid.uuid4())

        session = await _adk_session_service.create_session(
            app_name="clearsign",
            user_id=user_id,
        )

        user_content = types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                types.Part.from_text(text="이 임대차 계약서를 분석해주세요. 모든 조항을 추출하고, 표준 계약서와 비교하여 위험 조항을 찾고, 쉬운 한국어로 변환하고, 행동 스크립트를 생성하세요."),
            ],
        )

        import time
        result_text = None
        t0 = time.time()
        last_agent = None
        async for event in _adk_runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=user_content,
        ):
            # Log agent transitions
            agent_name = getattr(event, 'author', None) or ''
            if agent_name and agent_name != last_agent:
                elapsed = time.time() - t0
                if last_agent:
                    logger.info(f"[TIMING] Agent '{last_agent}' done at {elapsed:.1f}s")
                logger.info(f"[TIMING] Agent '{agent_name}' started at {elapsed:.1f}s")
                last_agent = agent_name
            if event.is_final_response() and event.content and event.content.parts:
                result_text = event.content.parts[0].text
        total = time.time() - t0
        logger.info(f"[TIMING] Pipeline total: {total:.1f}s (last agent: {last_agent})")

        # If no final response text, try session state
        if not result_text:
            session = await _adk_session_service.get_session(
                app_name="clearsign",
                user_id=user_id,
                session_id=session.id,
            )
            final = session.state.get("final_result")
            if final:
                result_text = final if isinstance(final, str) else json.dumps(final)

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

쉬운 한국어 변환 시 7대 원칙:
1. 통사 구조 재배열: 복합문→단문, 수동태→능동태
2. 조사 의존도 감소: "누가/무엇을/누구에게" 명시 분리
3. 조건/예외 분해: 중첩 조건→번호 매긴 개별 조건
4. 시간 전치: 기한/시기를 문장 맨 앞 배치
5. 한자어 법률 용어 분해: 원상회복→"집을 처음 상태로 고치는 것" 등
6. 행위자 중심 서술: 모든 문장에 명시적 주어
7. 공간적 정보 구조화: "누가|무엇을|언제|결과" 형태

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
        "level1": "쉬운 설명 (핵심 1-2문장, 7대 원칙 적용)",
        "level2": "비유 설명 (일상 비유)",
        "level3": "구체적 시나리오 (금액/상황 포함)"
      },
      "structuredBreakdown": {
        "who": "행위 주체",
        "what": "행위 내용",
        "when": "시기/기한",
        "condition": "조건",
        "result": "결과",
        "risk": "위험"
      },
      "termGlossary": [
        {
          "original": "법률 용어",
          "simple": "쉬운 설명",
          "context": "이 조항에서의 의미"
        }
      ],
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
      "status": "safe" 또는 "caution",
      "body": "조항 원문 전체"
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
        from google.genai import types

        client = _genai_client
        if client is None:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)

        response = await client.aio.models.generate_content(
            model="gemini-3-flash-preview",
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


@app.get("/api/config")
async def config():
    """Return public client-side configuration."""
    return JSONResponse(
        content={
            "googleClientId": GOOGLE_CLIENT_ID,
            "googleLoginEnabled": is_google_login_enabled(),
        }
    )


@app.post("/api/auth/google")
async def auth_google(payload: GoogleAuthRequest):
    if not is_google_login_enabled():
        return JSONResponse(
            status_code=503,
            content={"error": "Google login is not configured"},
        )

    credential = (payload.credential or "").strip()
    if not credential:
        return JSONResponse(
            status_code=400,
            content={"error": "credential is required"},
        )

    user = await _verify_google_credential(credential)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid Google credential"},
        )

    try:
        response = JSONResponse(content={"user": user})
        _set_session_cookie(response, user)
        return response
    except Exception as e:
        logger.error(f"Failed to create session cookie: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to create session"},
        )


@app.get("/api/auth/me")
async def auth_me(request: Request):
    user = _read_session_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"},
        )
    return JSONResponse(content={"user": user})


@app.post("/api/auth/logout")
async def auth_logout():
    response = JSONResponse(content={"ok": True})
    _clear_session_cookie(response)
    return response


@app.get("/api/demo")
async def demo():
    """Return pre-built fallback analysis for demo."""
    return JSONResponse(content=load_fallback())


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """Upload contract file → ADK pipeline → fallback chain → JSON response."""
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={"error": "파일이 너무 큽니다 (최대 20MB)"},
        )

    mime_type = file.content_type or "application/pdf"

    # Normalize mime types
    MIME_MAP = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".heic": "image/heic",
        ".heif": "image/heif",
        ".html": "text/html",
        ".htm": "text/html",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".rtf": "text/rtf",
    }
    if mime_type == "application/octet-stream":
        ext = os.path.splitext(file.filename or "")[1].lower()
        mime_type = MIME_MAP.get(ext, mime_type)

    logger.info(f"Analyzing file: {file.filename} ({mime_type}, {len(file_bytes)} bytes)")

    # Attempt 1: Single Gemini call (fast, no ADK overhead)
    try:
        result = await asyncio.wait_for(
            run_single_gemini(file_bytes, mime_type),
            timeout=SINGLE_CALL_TIMEOUT,
        )
        if result:
            result["analysisMode"] = "real"
            return JSONResponse(content=result)
    except asyncio.TimeoutError:
        logger.warning("Single Gemini timed out")
    except Exception as e:
        logger.error(f"Single Gemini attempt failed: {e}")

    # Attempt 2: ADK Pipeline (slower but more thorough)
    try:
        result = await asyncio.wait_for(
            run_adk_pipeline(file_bytes, mime_type),
            timeout=TIMEOUT_SECONDS,
        )
        if result:
            result["analysisMode"] = "real"
            return JSONResponse(content=result)
    except asyncio.TimeoutError:
        logger.warning("ADK pipeline timed out")
    except Exception as e:
        logger.error(f"ADK attempt failed: {e}")

    # Attempt 3: Static fallback (always succeeds)
    logger.info("Returning static fallback")
    fallback = load_fallback()
    fallback["analysisMode"] = "fallback"
    return JSONResponse(content=fallback)


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


COMPREHENSION_PROMPT = """당신은 농인·난청인 대상 문서 이해도 검증 전문가입니다.
ISO 24495-1의 Find-Understand-Use 프레임워크에 기반하여
쉬운 한국어로 변환된 계약서 설명의 이해도를 검증하는 문항을 생성하세요.

## 배경
- Cloze Test는 농인 대상 타당도/신뢰도가 검증된 이해도 측정 도구입니다.
- 채점 시 철자 오류, 조사 차이, 동의어는 모두 정답으로 처리합니다 (의미 기반 유연 채점).

## 채점 기준 생성 규칙
각 Cloze 문항에 대해:
- acceptableSynonyms: 정답의 동의어, 유의어 목록
- scoringNote: "의미 일치 여부만 판단. 철자·조사 오류 허용."

## 입력 데이터

위험 분석 결과:
{risk_analysis}

최종 분석 결과:
{final_result}

## 출력 JSON 형식

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


@app.post("/api/comprehension")
async def comprehension(request: Request):
    """Lazy-loaded comprehension quiz generation — separate from main pipeline."""
    try:
        body = await request.json()
        risk_analysis = body.get("risk_analysis", "{}")
        final_result = body.get("final_result", "{}")

        if isinstance(risk_analysis, dict):
            risk_analysis = json.dumps(risk_analysis, ensure_ascii=False)
        if isinstance(final_result, dict):
            final_result = json.dumps(final_result, ensure_ascii=False)

        prompt = COMPREHENSION_PROMPT.format(
            risk_analysis=risk_analysis,
            final_result=final_result,
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )

        result_text = response.text
        if not result_text:
            return JSONResponse(status_code=500, content={"error": "Empty response"})

        data = json.loads(result_text)
        return JSONResponse(content=data)

    except Exception as e:
        logger.error(f"Comprehension generation error: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "이해도 문항 생성에 실패했습니다."},
        )


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
