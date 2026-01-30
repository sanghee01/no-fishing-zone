# Search-AI

Aegis Link 프로젝트의 **지능형 도메인 홉 크롤러**입니다.

> **Note**: 이 서비스는 Claude API를 직접 사용하지 않습니다.  
> `react-ai` 서버를 통해 간접적으로 AI 분석을 수행합니다.

---

## 🎯 핵심 기능

1. **도메인 홉 전략**: 동일 도메인 연속 방문을 방지하여 차단 회피
2. **키워드 우선순위**: 도박/피싱 관련 키워드가 포함된 URL 우선 탐색
3. **AI 분석 파이프라인**: react-ai 서버와 연동하여 실시간 위협 분석
4. **Self-Feeding**: 큐가 비면 DB에서 미분석 URL을 자동 주입
5. **정적 데이터 적재**: PhishTank 블랙리스트 자동 로드

---

## 📁 프로젝트 구조

```
search-ai/
├── main.py              # 엔트리포인트
├── pyproject.toml       # 의존성 정의
├── Dockerfile           # Docker 이미지 빌드
├── crawler/             # 크롤링 엔진
│   ├── engine.py        # 비동기 크롤러 코어
│   ├── domain_hopper.py # 도메인 홉 전략 + 우선순위 큐
│   └── link_extractor.py # HTML 링크 추출
├── api_client/          # API 통신
│   ├── react_ai_client.py  # react-ai 서버 통신
│   └── backend_client.py   # Rust 백엔드 통신
├── collectors/          # 정적 데이터 수집
│   └── static_worker.py # PhishTank/화이트리스트 로더
├── utils/               # 유틸리티
│   ├── url_normalizer.py # URL 정규화
│   ├── headers.py        # User-Agent 로테이션
│   └── logging_config.py # 로깅 설정
├── seeds/               # 시드 데이터
│   ├── entry_points.txt  # 엔트리 URL 목록
│   ├── keywords.txt      # 우선순위 키워드
│   └── pished_tank.json  # PhishTank 블랙리스트
└── logs/                # 로그 저장
```

---

## 🚀 실행 방법

### 방법 1: Docker Compose로 전체 스택 실행 (권장)

```bash
# 1. 현재 실행 중인 컨테이너 중지
Ctrl+C  # 또는
docker compose down

# 2. 전체 서비스 빌드 및 실행 (search-ai 포함)
docker compose up -d --build

# 3. search-ai 로그 확인
docker compose logs -f search-ai

# 4. 특정 서비스만 재시작
docker compose restart search-ai
```

### 방법 2: search-ai만 단독 실행

```bash
# 다른 서비스가 이미 실행 중일 때
docker compose up search-ai

# 또는 1회 실행 후 종료
docker compose run --rm search-ai
```

### 방법 3: 로컬 개발 (Docker 없이)

```bash
cd search-ai

# 의존성 설치 (uv 필요)
uv sync

# 환경 변수 설정 (로컬용)
export REACT_AI_URL=http://localhost:8001
export BACKEND_URL=http://localhost:8000

# 실행
uv run python main.py
```

---

## ⚙️ 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `REACT_AI_URL` | react-ai 서버 URL | `http://ai:8001` |
| `BACKEND_URL` | Rust 백엔드 URL | `http://api:8000` |
| `SEEDS_DIR` | 시드 디렉토리 경로 | `/app/seeds` |
| `MAX_URLS` | 최대 처리 URL 수 | `500` |
| `SKIP_STATIC_IMPORT` | 정적 데이터 적재 건너뛰기 | `false` |

---

## 🔗 서비스 의존성

```
┌─────────────┐     HTTP      ┌─────────────┐     Claude API     ┌─────────────┐
│  search-ai  │ ───────────▶  │  react-ai   │ ─────────────────▶ │   Claude    │
│  (크롤러)    │     :8001     │  (분석 서버)  │                    │   (LLM)     │
└─────────────┘               └─────────────┘                    └─────────────┘
       │
       │ HTTP :8000
       ▼
┌─────────────┐               ┌─────────────┐
│   backend   │ ────────────▶ │  postgres   │
│  (Rust API) │    SeaORM     │    (DB)     │
└─────────────┘               └─────────────┘
```

**중요**: `search-ai`는 `ANTHROPIC_API_KEY`가 필요 없습니다!  
Claude API 호출은 `react-ai`가 담당합니다.

---

## 📊 크롤링 전략 플로우

```
1. Entry Points 로드 (entry_points.txt)
        ↓
2. URL 선택 (도메인 홉: 최근 방문 도메인 회피)
        ↓
3. HTTP 요청 (User-Agent 로테이션)
        ↓
4. 외부 링크 추출 (tldextract로 Apex 도메인 분리)
        ↓
5. 키워드 필터링 → 우선순위 부여
        ↓
6. AI 분석 요청 (react-ai)
        ↓
7. DB 저장 (Rust 백엔드)
        ↓
8. BLOCK/WARNING 시 → 해당 사이트 내부 링크도 탐색
        ↓
(반복)
```

---

## 📬 다른 팀 에이전트를 위한 연동 가이드

### Backend 팀에게

**search-ai가 호출하는 API 엔드포인트:**

```
POST http://api:8000/url-reputations/
Content-Type: application/json

{
  "url": "https://example.com",
  "score": 85,
  "status": "BLOCK",  // "SAFE" | "WARNING" | "BLOCK"
  "description": "PhishTank 블랙리스트"
}
```

**응답 형식 (현재 backend가 반환하는):**
```json
{
  "url": "https://example.com",
  "score": 85,
  "status": "BLOCK",
  "description": "PhishTank 블랙리스트"
}
```

**요청 사항 (Self-Feeding 기능을 위해 필요):**
```
GET http://api:8000/url-reputations/unanalyzed?limit=50
```
→ 아직 충분히 분석되지 않은 URL 목록을 반환하는 엔드포인트가 있으면 Self-Feeding 기능이 완성됩니다.

---

### React-AI 팀에게

**search-ai가 호출하는 API 엔드포인트:**

```
POST http://ai:8001/analyze
Content-Type: application/json

{
  "url": "https://suspicious-site.com",
  "request_id": "uuid-string"
}
```

**기대하는 응답 형식:**
```json
{
  "url": "https://suspicious-site.com",
  "status": "BLOCK",
  "risk_score": 85,
  "category": "Negative",
  "keyword": "토토",
  "reasons": ["New domain (+15)", "Suspicious TLD (+10)"]
}
```

**주의사항:**
- search-ai는 `asyncio.Semaphore(10)`으로 동시 요청을 제한합니다
- 타임아웃: 60초

---

### Database 팀에게

**search-ai가 사용하는 테이블:**

```sql
-- url_reputations 테이블 (이미 존재)
CREATE TABLE url_reputations (
  url TEXT PRIMARY KEY,
  description TEXT,
  score INTEGER NOT NULL,
  status VARCHAR(10) NOT NULL  -- 'SAFE', 'WARNING', 'BLOCK'
);
```

**대량 데이터 처리:**
- PhishTank 데이터 (28MB, 수만 개 URL)를 1,000개씩 Batch Insert
- 각 배치 사이 0.1초 딜레이로 DB 부하 관리
- ON CONFLICT (url) DO UPDATE 처리 필요 (이미 구현됨 ✅)

---

### Frontend 팀에게

search-ai는 백그라운드 서비스로, 직접적인 프론트엔드 연동이 없습니다.  
다만, search-ai가 수집한 데이터는 backend API를 통해 조회할 수 있습니다.

**크롤링 상태 모니터링 (선택적 구현):**
```
GET /api/crawler/status
→ { "queue_size": 1234, "analyzed": 500, "blocked": 123 }
```
이 엔드포인트를 backend에 추가하면 대시보드에서 크롤링 진행 상황을 표시할 수 있습니다.

---

## 🐛 트러블슈팅

### 1. "Connection refused" 오류
```
❌ AI Server connection error: Connection refused
```
→ react-ai 서비스가 실행 중인지 확인: `docker compose ps`

### 2. Backoff 로그가 많이 찍힐 때
```
🚫 Backoff 시작: example.com (30분)
```
→ 정상 동작입니다. 403/429 응답을 받으면 해당 도메인을 30분간 피합니다.

### 3. PhishTank 로드 오류
```
❌ PhishTank JSON 파싱 오류
```
→ `seeds/pished_tank.json` 파일 형식 확인

---

## 📝 개발자 노트

- Python 3.12+ 필요
- `uv` 패키지 매니저 사용
- 비동기 기반 (asyncio + httpx)
- 로그 파일: `logs/crawler_YYYYMMDD.log`
