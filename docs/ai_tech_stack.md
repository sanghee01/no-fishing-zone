# Aegis Link AI 기술스택

> AI 기반 URL 분석 및 피싱 탐지 시스템의 기술 구성

---

## 🔬 react-ai (URL 분석 AI 서버)

### 핵심 기술

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.13 | 런타임 |
| **FastAPI** | 0.128+ | REST API 프레임워크 |
| **Anthropic Claude 4.5 Haiku** | - | LLM 시맨틱 분석 |
| **Uvicorn** | 0.40+ | ASGI 서버 |

### 분석 라이브러리

| 기술 | 용도 |
|------|------|
| **httpx** | 비동기 HTTP 클라이언트 (리다이렉트 추적) |
| **BeautifulSoup4** | HTML 파싱/전처리 |
| **python-whois** | 도메인 WHOIS 조회 (도메인 나이 분석) |
| **tldextract** | TLD/도메인 추출 |
| **python-levenshtein** | 문자열 유사도 (타이포스쿼팅 탐지) |

---

## 🕷️ search-ai (크롤러/수집기)

### 핵심 기술

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.13 | 런타임 |
| **Playwright** | 1.48.0 | 헤드리스 브라우저 (JS 렌더링) |
| **httpx** | 0.28+ | API 호출 (HTTP/2 지원) |

### 수집 라이브러리

| 기술 | 용도 |
|------|------|
| **BeautifulSoup4** | HTML 파싱 |
| **tldextract** | Apex 도메인 추출 |
| **fake-useragent** | User-Agent 로테이션 (봇 탐지 우회) |
| **aiofiles** | 비동기 파일 I/O |
| **certstream** | SSL 인증서 실시간 감청 |

---

## 🏗️ 아키텍처 특징

### 사용한 기술
- **Anthropic SDK 직접 호출**: 경량화 및 빠른 응답 속도
- **비동기 처리 (asyncio)**: 대량 URL 동시 분석
- **Docker 컨테이너화**: 환경 독립성 확보

### 사용하지 않은 기술
- **LangChain**: 미사용 (직접 SDK 호출로 충분)
- **OpenAI API**: 미사용 (Anthropic Claude만 사용)
- **Vector DB**: 미사용 (RAG 불필요)

---

## 📊 LLM 모델 정보

| 항목 | 값 |
|------|-----|
| **Provider** | Anthropic |
| **Model** | Claude 4.5 Haiku |
| **용도** | 웹페이지 시맨틱 분석, 피싱 패턴 탐지 |
| **선정 이유** | 빠른 응답 속도, 저렴한 비용, 충분한 성능 |

---

## 🎯 기술 선택 근거

1. **LangChain 미사용 이유**
   - 단순 LLM 호출에는 오버헤드만 증가
   - 직접 SDK 호출로 응답 속도 최적화
   - RAG 불필요 (실시간 분석 위주)

2. **Claude Haiku 선택 이유**
   - 실시간 분석에 적합한 빠른 응답
   - 대량 요청 처리에 적합한 비용
   - 피싱 패턴 감지에 충분한 성능

3. **Playwright 선택 이유**
   - JavaScript 렌더링 필수 (최신 피싱 사이트)
   - 리다이렉트 추적 용이
   - 안정적인 브라우저 자동화
