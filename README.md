# ClearSign — 임대차 계약서 위험 분석 AI

> 농인·난청인을 위한 임대차 계약서 위험 분석 서비스

임대차 계약서를 업로드하면 국토교통부 표준 계약서와 비교하여 **위험 조항을 자동 탐지**하고, **쉬운 한국어 3단계 설명**과 **행동 스크립트**를 생성합니다.

## 주요 기능

- **계약서 업로드 & AI 분석** — PDF, 이미지, HTML 등 다양한 형식 지원
- **위험 조항 탐지** — 표준 계약서 대비 이탈도 점수화 (0~100)
- **쉬운 한국어 3단계 변환** — 핵심 설명 → 비유 설명 → 시나리오
- **행동 스크립트 생성** — 위험 조항별 수정 요청 문구 제공
- **전세사기 검색** — Google Search Grounding 기반 지역 사기 이력 조회
- **이해도 검증 퀴즈** — Cloze Test 기반 계약 내용 이해 확인
- **관점 전환 UI** — 임차인/임대인 관점으로 계약서 분석

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, Python 3.12 |
| AI | Google Gemini 3 (ADK 3-Agent Pipeline) |
| Frontend | Tailwind CSS, Chart.js, Vanilla JS |
| 배포 | Docker, Google Cloud Run |

## 아키텍처

```
[계약서 업로드]
      ↓
┌─────────────────────────────┐
│  ADK 3-Agent Pipeline       │
│  ┌─────────────────────┐    │
│  │ Agent 1: Parser      │───→ 조항 추출
│  │ Agent 2: Analyzer    │───→ 위험 분석
│  │ Agent 3: Translator  │───→ 쉬운 변환 + 행동 스크립트
│  └─────────────────────┘    │
└─────────────────────────────┘
      ↓ (폴백 체인)
  ADK → 단일 Gemini 호출 → 사전 분석 JSON
```

## 실행 방법

### 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 입력

# 3. 서버 시작
python main.py
```

http://localhost:8080 에서 접속 가능

### Docker

```bash
docker build -t clearsign .
docker run -p 8080:8080 -e GEMINI_API_KEY=your-key clearsign
```

### Cloud Run 배포

```bash
gcloud run deploy clearsign \
  --source . \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key
```

## 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `GEMINI_API_KEY` | O | Google Gemini API 키 |
| `GOOGLE_CLIENT_ID` | - | Google OAuth 클라이언트 ID |
| `SESSION_SECRET` | - | 세션 암호화 키 |

## 데모

`data/` 폴더에 테스트용 샘플 계약서가 포함되어 있습니다. API 키 없이도 사전 분석된 데모 데이터로 UI를 체험할 수 있습니다.

## 라이선스

MIT License
