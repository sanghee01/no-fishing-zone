# Aegis Link

**URL 평판 관리 및 스캠 탐지 시스템** - MSA 기반 보안 솔루션

사용자를 피싱, 도박, 스캠 사이트로부터 보호하는 지능형 URL 분석 플랫폼입니다.

---

## 🏗️ 프로젝트 구조

```
aegis-link/
├── 📄 docker-compose.yml     # 전체 서비스 오케스트레이션
├── 📄 .env                   # 환경변수 (Git 제외)
├── 📄 AGENT.md               # AI 에이전트 행동 지침
├── 📄 README.md              # 이 파일
│
├── 📁 .agent/                # AI 에이전트 설정
│   ├── rules/                # 코딩 규칙 (docker, vespera, vespertide)
│   ├── skills/               # 기술 가이드
│   └── workflows/            # 자동화 워크플로우
│
├── 📁 backend/               # 🦀 Rust API 서버 (메인 서버)
│   ├── src/
│   │   ├── main.rs           # 엔트리포인트
│   │   ├── routes/           # API 라우트 핸들러
│   │   └── models/           # SeaORM 모델
│   ├── migrations/           # DB 마이그레이션
│   ├── Dockerfile
│   └── Cargo.toml
│
├── 📁 frontend/              # ⚛️ Next.js 프론트엔드
│   ├── app/                  # App Router 페이지
│   ├── components/           # React 컴포넌트
│   ├── lib/                  # 유틸리티
│   ├── Dockerfile
│   └── package.json
│
├── 📁 react-ai/              # 🤖 Python AI 분석 서버
│   ├── app/
│   │   ├── main.py           # FastAPI 엔트리포인트
│   │   ├── services/         # 분석 로직 (Claude AI 연동)
│   │   └── models.py         # Pydantic 스키마
│   ├── Dockerfile
│   └── pyproject.toml
│
└── 📁 search-ai/             # 🕷️ 지능형 도메인 홉 크롤러
    ├── main.py               # 엔트리포인트
    ├── crawler/              # 크롤링 엔진
    ├── api_client/           # API 통신 클라이언트
    ├── collectors/           # 정적 데이터 수집
    ├── utils/                # 유틸리티
    ├── seeds/                # 시드 데이터 (엔트리포인트, 키워드, 블랙리스트)
    │   ├── entry_points.txt  # 크롤링 시작점 URL
    │   ├── keywords.txt      # 우선순위 키워드
    │   ├── pished_tank.json  # PhishTank 블랙리스트 (28MB)
    │   └── 1000000white.csv  # Tranco 화이트리스트 (21MB)
    ├── logs/                 # 크롤링 로그
    ├── Dockerfile
    └── pyproject.toml
```

---

## 🔄 아키텍처 및 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Aegis Link 시스템                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                              ┌──────────────┐        │
│  │   Frontend   │ ◄──── HTTP :3001 ────────►  │    User      │        │
│  │  (Next.js)   │                              │   Browser    │        │
│  └──────┬───────┘                              └──────────────┘        │
│         │                                                               │
│         │ HTTP :8000                                                    │
│         ▼                                                               │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐   │
│  │   Backend    │ ◄─────► │   react-ai   │ ◄─────► │  Claude AI   │   │
│  │ (Rust/Axum)  │  :8001  │   (FastAPI)  │   API   │   (LLM)      │   │
│  └──────┬───────┘         └──────────────┘         └──────────────┘   │
│         │                         ▲                                    │
│         │ SeaORM                  │ HTTP :8001                         │
│         ▼                         │                                    │
│  ┌──────────────┐         ┌──────┴───────┐                            │
│  │  PostgreSQL  │ ◄─────  │  search-ai   │  (크롤러)                   │
│  │    (DB)      │  :8000  │  (Python)    │                            │
│  └──────────────┘         └──────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ 데이터베이스

### 위치
- **호스트**: Docker 컨테이너 `aegis-link-postgres-1`
- **외부 포트**: `localhost:5432`
- **내부 포트**: `postgres:5432` (Docker 네트워크)

### 접속 정보
| 항목 | 값 |
|------|------|
| Database | `aegis_link_db` |
| User | `aegis_user` |
| Password | `.env`의 `POSTGRES_PASSWORD` |

### 주요 테이블
```sql
-- URL 평판 정보 테이블
CREATE TABLE url_reputations (
    url TEXT PRIMARY KEY,           -- 정규화된 URL
    description TEXT,               -- 설명/분석 결과
    score INTEGER NOT NULL,         -- 위험 점수 (0-100)
    status VARCHAR(10) NOT NULL     -- 'SAFE', 'WARNING', 'BLOCK'
);
```

### 직접 접속 명령어
```bash
# PostgreSQL CLI 접속
docker exec -it aegis-link-postgres-1 psql -U aegis_user -d aegis_link_db

# 데이터 조회
docker exec -it aegis-link-postgres-1 psql -U aegis_user -d aegis_link_db -c "SELECT COUNT(*) FROM url_reputations;"

# 수동 데이터 삽입
docker exec -it aegis-link-postgres-1 psql -U aegis_user -d aegis_link_db -c \
  "INSERT INTO url_reputations (url, description, score, status) VALUES ('https://example.com', '테스트', 100, 'SAFE');"
```

---

## 🚀 빠른 시작

### 사전 준비
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 및 실행
- [Node.js](https://nodejs.org/) (v18 이상) - 로컬 개발 시

### 1. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 설정:
# - POSTGRES_PASSWORD=your_password
# - ANTHROPIC_API_KEY=your_claude_api_key
```

### 2. 전체 서비스 실행
```bash
# 빌드 및 실행
docker compose up -d --build

# 상태 확인
docker compose ps

# 로그 확인 (전체)
docker compose logs -f

# 특정 서비스 로그
docker compose logs -f search-ai
```

### 3. 접속 주소
| 서비스 | URL | 설명 |
|--------|-----|------|
| Frontend | http://localhost:3001 | 사용자 인터페이스 |
| Backend API | http://localhost:8000 | REST API |
| AI Server | http://localhost:8001 | AI 분석 API |
| Swagger Docs | http://localhost:8000/docs | API 문서 |

---

## 🔧 서비스 포트

| 서비스 | 포트 | 설명 | Docker 서비스명 |
|--------|------|------|-----------------|
| backend | 8000 | Rust API 서버 | `api` |
| react-ai | 8001 | Python AI 분석 서버 | `ai` |
| frontend | 3001 | Next.js 프론트엔드 | `frontend` |
| postgres | 5432 | PostgreSQL 데이터베이스 | `postgres` |
| search-ai | - | 크롤러 (포트 없음, 백그라운드) | `search-ai` |

---

## 📝 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Backend** | Rust, Axum, SeaORM, Vespera, Tower-HTTP |
| **Frontend** | Next.js 15 (App Router), TypeScript |
| **AI Analysis** | Python, FastAPI, Claude API (Anthropic) |
| **Crawler** | Python, httpx, BeautifulSoup4, tldextract |
| **Database** | PostgreSQL 16 |
| **DevOps** | Docker, Docker Compose |

---

## 💻 개발 가이드

### 백엔드 (Rust)
- **CORS 설정**: `tower-http`를 이용한 Permissive CORS
- **API 로그**: `println!`을 통해 터미널에서 실시간 확인
- **DB 마이그레이션**: 서버 시작 시 자동 실행
- **Rust Nightly** 환경에서 빌드

### 프론트엔드 (Next.js)
- **API 연동**: `@devup-api/fetch`로 타입 안전한 API 호출
- **예외 처리**: 404 응답 시 안내 UI 표시

### Search-AI (크롤러)
- **정적 데이터**: PhishTank, Tranco 리스트 자동 로드
- **동적 크롤링**: 도메인 홉 전략으로 차단 회피
- **Self-Feeding**: 큐가 비면 DB에서 미분석 URL 자동 주입

---

## 📄 라이선스

MIT
