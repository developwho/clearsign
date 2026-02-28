## 0) 서울 해커톤에서 요구되는 ‘게임의 룰’부터 고정하기

서울은 단순 아이디어톤이 아니라 **Production Sprint(프로덕션 스프린트)** 성격이 강합니다. 핵심은 “행사 당일, 실제로 구동 가능한 앱을 **GCP 상에 배포**”하는 데 초점이 있다는 점입니다. ([매일경제][1])
또한 Google DeepMind/AI Futures Fund/AttentionX 공동 주최, **Antigravity + AI Studio + Vertex AI**를 활용해 Gemini 3의 추론·멀티모달을 극대화하는 방향을 명시하고 있습니다. ([매일경제][1])
팀은 최대 4명, 승인제(사전 신청 후 승인)이며, 상금은 **$150,000 상당 Gemini API 크레딧 + AI Futures Fund 창립자 30분 콜**이 서울에도 동일하게 언급됩니다. ([매일경제][1])

**즉, 서울 해커톤의 “정답 형태”는:**

* (1) **배포된 서비스 URL**이 있고(데모가 아니라 “작동하는 제품”) ([매일경제][1])
* (2) Gemini 3를 “중심 엔진”으로 쓰며(부가 기능 X) ([매일경제][1])
* (3) Hard Tech & Entertainment 맥락에서 “와우 + 실사용”을 동시에 보여주는 것 ([Cerebral Valley][2])

---

## 1) 투어(도시별) 포맷: 무엇이 공통인가

Cerebral Valley가 공개한 APAC 투어 안내 기준, 아시아에서는 **Bengaluru(2/14) → Tokyo(2/21) → Seoul(2/28) → Singapore(3/7)**로 “멀티-시티 인퍼슨 투어”가 잡혀 있었습니다. ([Cerebral Valley][3])
각 도시는 대체로:

* 승인제 / 인원 제한 / 팀 최대 4명 ([Cerebral Valley][4])
* AI Studio, Vertex AI, Antigravity를 전면에 둠 ([Cerebral Valley][4])
* 우승 혜택: 대규모 크레딧 + AI Futures Fund 콜 ([Cerebral Valley][3])

**서울은 여기에 “Hard Tech & Entertainment”라는 로컬 테마가 더 강하게 걸린 도시**입니다. ([Cerebral Valley][2])

---

## 2) “이미 열렸던 대회”에서 뽑는 승리 패턴

여기서부터가 핵심입니다. 정보가 특히 풍부한 2개(싱가포르/도쿄)를 깊게 파고, 벵갈루루/글로벌 Devpost를 보조축으로 씁니다.

---

## 2.1 싱가포르(공개 데이터가 매우 풍부) — “7시간 안에 ‘완성도’로 이긴 팀들”

싱가포르에서는 (최소 한 차례) **2026-01-10**, 7시간 빌드로 **76개 프로젝트 / 189명**이 참여한 결과와 **우승작 리스트가 실명 수준으로 공개**돼 있습니다. ([t.co][5])

### 싱가포르 우승/수상작이 말해주는 것

**1st: Neuroflix** — “AI 감독/스태프가 있는 에이전틱 비디오 프로덕션(미디어 제작사 컨셉)” ([t.co][5])
**2nd: Ruban** — “2D 맵을 지형으로 변환 + 음성 가이드(멀티모달/보이스 UX)” ([t.co][5])
**3rd: Unmute** — “텍스트/음성 → 싱가포르 수어(3D 아바타) 번역(접근성/임팩트)” ([t.co][5])
**Most Bananas: Wayang Studio** — “싱글리시 AI NPC 어드벤처 게임(로컬 문화 + 엔터테인먼트)” ([t.co][5])

**Honorable Mention**도 방향성이 선명합니다:

* “방 스캔 → 재설계 → AR 뷰 + Gemini Live” (banana novate) ([t.co][5])
* PDF 학습 보조 + 시각적 수식 주석(RabbitHole) ([t.co][5])
* 연구용 Gemini IDE(Vibero) ([t.co][5])
* 결함 포렌식 탐지(Zer0) ([t.co][5])

➡️ 결론: **(A) 에이전틱 워크플로우, (B) 멀티모달/보이스/실시간, (C) 엔터테인먼트/로컬 감성, (D) “제품처럼 보이는 UX”**가 상위권을 강하게 점유합니다. ([t.co][5])

### 싱가포르 운영 포맷(트랙/심사)

싱가포르 Luma 페이지에는 트랙 구조(예: Generative Media, Deep Research 등), 일정(등록→빌드→코드 프리즈→데모), 상금 배분/심사 방식이 상세히 제시돼 있습니다. ([Luma][6])
(서울이 동일 트랙을 쓴다고 단정할 수는 없지만, “심사 구조/제출물 요구”는 투어 전반에서 재활용될 가능성이 큽니다.)

---

## 2.2 도쿄(2/21) — “금지 리스트”가 곧 ‘심사위원의 피로도 지도’

도쿄는 Supercell과 파트너십을 걸고 “게임/게임개발”을 전면 테마로 삼았습니다. ([Cerebral Valley][7])
그리고 도쿄 리포트(note)가 매우 강력한데, **운영 문서(룰북) 맥락, 금지 프로젝트 예시, 시간표, 상금 배분, 우승작**까지 담고 있습니다. ([note（ノート）][8])

### 도쿄에서 실제로 “하지 말라”는 것(중요)

도쿄 룰북 기반 리포트에 따르면, 금지 예시로:

* “기본적인 RAG 앱”
* “Streamlit 앱”
* “AI 멘탈헬스/영양코치/성격분석”
  등이 언급됩니다. ([note（ノート）][8])

➡️ 이건 서울에도 그대로 적용될 가능성이 높습니다.
왜냐하면 서울도 “프로덕션 스프린트 + DeepMind 심사/멘토 + Antigravity 활용”처럼 **‘AI 데모 흔한 거’에 대한 피로도가 누적된 포맷**이기 때문입니다. (서울 기사에서도 “실제 서비스 구현”을 반복 강조) ([매일경제][1])

### 도쿄 시간 구조(현장 빌드의 리얼)

도쿄 리포트 기준:

* 10:00 킥오프 → 17:00 제출 → 19:00 파이널 6팀 발표 → 20:15 결과 ([note（ノート）][8])
  즉, 겉으로는 9~22시 행사여도 **실제 ‘빌드 시간’은 7~8시간대**로 관리됩니다.

### 도쿄 우승작(“엔터테인먼트 + 멀티모달”의 정석)

* 1위: **Food Fight Robot** — 음식 사진을 로봇으로 변형/생성해 배틀(이미지 생성 + 3D 파이프라인까지) ([note（ノート）][8])
* 2위: **KAIJU VOICE** — 음성 인식/감정/독창성 평가로 싸우는 액션 게임(보이스+감정+BGM) ([note（ノート）][8])
* 3위: **プロンプ道場(PrompDojo)** — “프롬프트 역추적” 대전(이미지 생성 + 유사도 채점 + 피드백) ([note（ノート）][8])

➡️ 심사위원이 원하는 건 “AI로 ‘가능해진’ 새로운 인터랙션”입니다.
그냥 LLM을 붙인 게임이 아니라 **LLM/멀티모달이 게임 루프의 핵심 규칙을 담당**합니다. ([note（ノート）][8])

---

## 2.3 벵갈루루(2/14) — “멀티링구얼/로컬라이제이션”이 강한 신호

공식 페이지는 포맷(인퍼슨, 팀 4인, Antigravity/AI Studio/Vertex AI) 정도만 보이지만 ([Cerebral Valley][9])
참가자 회고(LinkedIn)에서 다음이 관측됩니다:

* 1500+ 지원, 462명 참석, 70개 최종 제출, 6개가 라운드2 진출(개인 회고 기반) ([LinkedIn][10])
* 킥오프에서 DeepMind DevRel이 **멀티모달 + 멀티링구얼**을 라이브로 강조(예: 이미지 보고 텔루구어 설명) ([LinkedIn][10])

➡️ 서울에서도 “한국 시장/언어/콘텐츠”를 단순 번역이 아니라 **기능 설계에 내재화**하면 가산점이 될 여지가 큽니다. (특히 Hard Tech & Entertainment 문맥에서 K-콘텐츠, 한국형 UX는 강력한 무기) ([Cerebral Valley][2])

---

## 2.4 글로벌 Devpost 해커톤(온라인) — 채점 가중치가 ‘정답지’에 가깝다

글로벌 Devpost 기준 심사 가중치가 매우 명확합니다:

* Technical Execution 40%
* Innovation/Wow 30%
* Potential Impact 20%
* Presentation/Demo 10% ([Gemini 3 Hackathon][11])

서울이 이 가중치를 1:1로 쓰는 건 아닐 수 있지만, **DeepMind 주관 + 제품 구현형 스프린트**인 이상 판단 기준은 크게 다르기 어렵습니다. ([매일경제][1])

---

## 3) 패턴 요약: “우승 확률을 올리는 6가지 조건”

위 데이터(싱가포르 수상작 리스트 + 도쿄 룰북/우승작 + Devpost 기준)를 합치면, 우승권은 대체로 아래를 만족합니다.

1. **‘기본형’은 즉시 탈락권**

* PDF RAG, 뻔한 챗봇, Streamlit 데모 느낌: 도쿄에서 아예 금지/피로도 폭발로 명시 ([note（ノート）][8])

2. **Gemini 3가 “기능이 아니라 시스템”이어야 함**

* 게임 마스터/심판/감독/에이전트 등, 핵심 루프를 맡김(도쿄 1~3위, 싱가포르 1위/Most Bananas) ([note（ノート）][8])

3. **멀티모달/실시간/에이전틱 중 최소 2개는 먹여야 함**

* 사진→3D/로봇, 음성→게임 룰, AR+Live 등 ([note（ノート）][8])

4. **프로덕션 스프린트답게 “배포/접속/재현”이 깔끔해야 함**

* 서울은 특히 “GCP 배포”를 명시 ([매일경제][1])

5. **데모가 ‘한 방에 이해’되어야 함**

* Devpost에서도 데모 10%가 별도 항목 ([Gemini 3 Hackathon][11])
* 실제 현장에선 10%가 아니라 **체감 50%**입니다(상위 6팀 선정 단계에서 “이해도”가 컷 기준이 되기 때문).

6. **로컬 감성/문화/시장 적합성은 “차별화 부스터”**

* 싱가포르 수상작에 로컬 언어/콘셉트(싱글리시 NPC)가 들어감 ([t.co][5])
* 벵갈루루에서 멀티링구얼/로컬라이즈가 강하게 언급 ([LinkedIn][10])

---

## 4) 서울(2/28)용 준비 전략: “우승 가능한 설계도”

### 4.1 서울 테마 해석: Hard Tech & Entertainment를 ‘기획 문장’으로 박기

서울은 “Hard Tech & Entertainment 교차점”을 명시합니다. ([Cerebral Valley][2])
이걸 가장 세게 먹이는 방식은:

* **Hard Tech(현실 세계 입력/제약)**: 카메라(비전), 마이크(오디오), 센서(모바일 IMU), 공간(AR), 물리 시뮬레이션(간접)
* **Entertainment(출력/경험)**: 게임 루프, 라이브 퍼포먼스, 인터랙티브 스토리, 크리에이터 툴(영상/음악/무대), 팬 경험

즉 “엔터 앱”이 아니라 **현실 입력이 들어오는 엔터 경험**이 승률이 높습니다. (도쿄/싱가포르 수상작과 정합) ([note（ノート）][8])

---

## 4.2 추천 프로젝트 컨셉 3개 (서울 우승권을 노릴만한, ‘하루 빌드 가능한’ 것)

아래 3개는 **(1) Hard Tech & Entertainment 적합, (2) 멀티모달/실시간/에이전틱 최소 2개 탑재, (3) GCP 배포 MVP가 하루에 가능**한 조합으로 설계했습니다. ([Cerebral Valley][2])

---

### 컨셉 A) Stage Director Agent: “공연/촬영을 ‘연출’하는 에이전틱 감독”

**한 줄:** 영상/무대/댄스 리허설을 입력(비디오/오디오/스크립트)으로 받아 **카메라 컷/조명/자막/하이라이트**를 자동 설계·리허설하는 “AI 연출감독”.

* **Hard Tech 입력:** 리허설 영상(카메라), 음악(오디오), 무대 동선(텍스트/스케치)
* **Entertainment 출력:** 컷 편집 플랜(타임라인), 하이라이트 릴, 자막/오버레이, 연출 지시서(콜시트)
* **Gemini 3 역할(핵심 루프):**

  * 멀티모달로 장면 분석 → “왜 하이라이트인지” 설명(추론)
  * 에이전틱 워크플로우로 “분석→플랜→생성→검수” 단계 분리
* **데모 플로우(30초 마법):** 리허설 영상 업로드 → 10초 내 “하이라이트 3개 + 컷 제안” 생성 → “원클릭 리허설 모드(타임라인 재생)”
* **GCP 배포:** Cloud Run(백엔드) + Cloud Storage(영상) + Firestore(프로젝트)
* **왜 승률 높나:** 싱가포르 1위가 ‘에이전틱 비디오 프로덕션’이었고 ([t.co][5]), 서울도 엔터테인먼트 강세. ([Cerebral Valley][2])

---

### 컨셉 B) Voice Combat Lab: “음성·감정·리듬이 ‘물리 스탯’이 되는 배틀”

**한 줄:** 마이크 입력을 받아 **음량/감정/발화 의도/리듬**을 실시간 분석해 스킬이 발동하는 “음성 액션 배틀(또는 파티게임)”.

* **Hard Tech 입력:** 실시간 마이크(오디오)
* **Entertainment 출력:** 즉시 피드백(스킬/이펙트/점수), 랭킹, 리플레이
* **레퍼런스 정합:** 도쿄 2위가 바로 “KAIJU VOICE” 유형(음성 기반 액션) ([note（ノート）][8])
* **차별화 포인트(서울용):**

  * 한국어 감정/억양/사투리/랩 플로우 등 “로컬 음성 특징”을 게임 규칙으로
  * “Hard Tech”를 살리려면: **실시간 + 지연(레이트턴시) 최소화**를 KPI로 내세우기
* **GCP 배포:** WebRTC/웹소켓 + Cloud Run + (가능하면) Vertex AI 경유

---

### 컨셉 C) AR Build-and-Remix: “현실 공간을 스캔해 ‘엔터 공간’으로 바꾸는 AR”

**한 줄:** 방/책상/전시 공간을 스캔하면, Gemini가 테마(게임방/스튜디오/무대)로 **재설계**하고 AR로 즉시 미리보기.

* **레퍼런스 정합:** 싱가포르 Honorable Mention에 “방 스캔→재설계→AR + Gemini Live”가 이미 검증됨 ([t.co][5])
* **서울 차별화:** “K-엔터 공간” 특화(연습실/팬존/홈스튜디오) + 쇼핑/제작 파이프라인(링크)
* **GCP 배포:** 프론트(WebAR) + 백엔드(Cloud Run) + 이미지/포인트클라우드 저장(Cloud Storage)

---

## 4.3 서울에서 “안전하게 상위 6팀” 들어가는 실행 플랜 (시간표 기반)

서울은 9:00~22:00 행사지만, 기사/타 도시 패턴상 **‘제출 마감은 17시대’**로 잡힐 가능성이 높습니다(도쿄 17:00 제출). ([note（ノート）][8])
그래서 **“16:00에 이미 배포 끝”**을 목표로 설계합니다.

### D-7 ~ D-1 (사전 준비: 규정 위반 없는 선에서)

* (기술) Cloud Run 배포 템플릿(Hello World), Firestore/Storage 권한, CI/CD “틀”만 준비
* (기획) 1페이지 PRD + 데모 스크립트 + 아키텍처 다이어그램(빈칸 템플릿)
* (팀) 역할 고정:

  * Builder1(백엔드/배포)
  * Builder2(프론트/UX)
  * Builder3(모델/프롬프트/에이전트)
  * Builder4(데모/피치/디자인)
* (리스크) “실시간/멀티모달”이 실패할 경우를 대비한 **폴백 데모(사전 녹화 영상/샘플 입력)** 준비

  * 해커톤은 라이브 환경이 흔들립니다. 폴백은 ‘보험’이지 ‘부정행위’가 아닙니다(코어 기능은 당일 구현).

### 행사 당일 타임박스(권장)

* 09:00~10:00: 체크인/네트워킹/멘토 파악
* 10:00~10:30: 문제정의 확정(“한 문장”) + MVP 스코프 잠금
* 10:30~12:30: **엔드투엔드 스켈레톤**(버튼→API→응답→UI) + 1차 배포
* 12:30~14:30: “매직 모먼트” 1개 완성(예: 영상 업로드→하이라이트 1개 생성)
* 14:30~16:00: 안정화(실패 처리/로딩/캐시/로그) + 2차 배포
* 16:00~17:00: 데모 스크립트 리허설 + 스크린레코딩(있으면) + 제출물 정리
* 17:00 이후: 파이널 대비(6팀 발표 구조 대비: 3분 피치 + 2분 Q&A를 가정)

---

## 4.4 “심사 항목 역산”으로 만드는 제출물/피치 구조

Devpost의 채점 프레임(기술 40 / 와우 30 / 임팩트 20 / 데모 10)을 서울에도 그대로 적용해 설계하면 안전합니다. ([Gemini 3 Hackathon][11])

### (1) Technical Execution 40%를 먹는 법

* “GCP 배포 URL”을 첫 장에 박기(서울은 배포 요구를 명시) ([매일경제][1])
* 아키텍처 다이어그램 1장: 입력 → Gemini(모델/에이전트) → 저장/처리 → UI
* 실패 처리/관찰가능성: 최소한 request id, 에러 메시지, 로그(Cloud Logging) 정도는 보여주기

### (2) Innovation/Wow 30%를 먹는 법

* 도쿄가 금지한 “기본 RAG / Streamlit” 계열 피하기 ([note（ノート）][8])
* “AI가 없으면 불가능한 룰/경험”을 정의:

  * 게임이면 **심판/GM/룰 생성자**가 AI
  * 크리에이터 툴이면 **감독/편집자/제작자**가 AI ([t.co][5])

### (3) Potential Impact 20%를 먹는 법

* 엔터테인먼트라도 “시장/유저”를 구체화:

  * 크리에이터(1인 제작자) / 공연 제작 / 게임 스트리머 / 팬덤 / 교육(댄스/보컬) 등
* 서울은 AttentionX 참여. “사업화 질문”이 들어올 수 있으니 “누가 돈 내나” 한 줄 준비. ([매일경제][1])

### (4) Presentation/Demo 10%를 먹는 법

* 도입 15초: 문제 → 1문장 솔루션
* 라이브 60초: 매직 모먼트 1번만 시연
* 마무리 15초: Gemini 3를 어떻게 썼는지(멀티모달/추론/에이전틱/실시간) 요약
  (서울은 Antigravity/AI Studio/Vertex AI를 활용하라고 구체 도구를 열거합니다. 이 언어를 발표에 그대로 쓰세요.) ([매일경제][1])

---

## 5) 서울에서 “절대 하면 안 되는 실수” 체크리스트

* “그냥 챗봇 + PDF” (도쿄에서 금지/피로도 최상) ([note（ノート）][8])
* 배포 실패(서울은 GCP 배포를 요구) ([매일경제][1])
* 로그인/온보딩 때문에 데모가 막힘(심사 시간은 짧습니다)
* 모델이 하는 일이 ‘장식’ 수준(“우린 Gemini를 써요”가 아니라 “Gemini가 제품을 운영한다”) ([t.co][5])
* 발표에서 “Hard Tech & Entertainment” 연결이 약함(서울의 차별점) ([Cerebral Valley][2])

---

[1]: https://www.mk.co.kr/news/it/11970218 "https://www.mk.co.kr/news/it/11970218"
[2]: https://cerebralvalley.beehiiv.com/p/developers-across-seoul-gemini-3-is-coming-in-hot "https://cerebralvalley.beehiiv.com/p/developers-across-seoul-gemini-3-is-coming-in-hot"
[3]: https://cerebralvalley.beehiiv.com/p/developers-across-asia-gemini-3-is-landing-cf89 "https://cerebralvalley.beehiiv.com/p/developers-across-asia-gemini-3-is-landing-cf89"
[4]: https://cerebralvalley.ai/e/gemini-3-nyc-hackathon "https://cerebralvalley.ai/e/gemini-3-nyc-hackathon"
[5]: https://t.co/atrzBabHde "https://t.co/atrzBabHde"
[6]: https://luma.com/gemini3sgp "https://luma.com/gemini3sgp"
[7]: https://cerebralvalley.ai/e/gemini-3-tokyo-hackathon "https://cerebralvalley.ai/e/gemini-3-tokyo-hackathon"
[8]: https://note.com/aicu/n/nccb00d048145 "https://note.com/aicu/n/nccb00d048145"
[9]: https://cerebralvalley.ai/e/gemini-3-bengaluru-hackathon "https://cerebralvalley.ai/e/gemini-3-bengaluru-hackathon"
[10]: https://www.linkedin.com/posts/nishith-p_gemini3-googledeepmind-hackathon-activity-7430135339156996096-GJYa "https://www.linkedin.com/posts/nishith-p_gemini3-googledeepmind-hackathon-activity-7430135339156996096-GJYa"
[11]: https://gemini3.devpost.com/ "https://gemini3.devpost.com/"
