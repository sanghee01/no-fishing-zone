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

| 서비스       | URL                               | 설명                           |
| ------------ | --------------------------------- | ------------------------------ |
| Frontend     | http://localhost                  | 사용자 인터페이스 (Nginx 경유) |
| Backend API  | http://localhost/url-reputations/ | REST API (Nginx 경유)          |
| Health Check | http://localhost/health/          | 서비스 상태 확인               |

---

## 🚀 팀원용 빠른 시작 (5분 설치)

### 사전 준비

1. **Docker Desktop 설치**
   - [다운로드 링크](https://www.docker.com/products/docker-desktop/)
   - 설치 후 Docker Desktop 실행 확인

2. **환경 변수 파일 준비**
   - 팀 리더에게 `.env` 파일 요청
   - 또는 `.env.example`을 복사하여 직접 설정

---

### 설치 단계

#### Step 1: 저장소 클론

```bash
# 1. 원하는 디렉토리로 이동
cd ~/Documents

# 2. 저장소 클론
git clone https://github.com/your-org/aegis-link.git
cd aegis-link
```

#### Step 2: 환경 변수 설정

**옵션 A: 팀 리더에게 받은 .env 파일 사용**

```bash
# .env 파일을 프로젝트 루트에 복사
# (파일 탐색기에서 드래그 앤 드롭)
```

**옵션 B: 직접 설정**

```bash
# 1. 템플릿 복사
cp .env.example .env

# 2. 에디터로 열기
nano .env  # 또는 code .env (VS Code)

# 3. 다음 값 설정
# POSTGRES_PASSWORD=your_password
# ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXX  (Anthropic Console에서 발급)
# NEXT_PUBLIC_API_BASE_URL=http://localhost/
```

#### Step 3: 배포 스크립트 실행

```bash
# 배포 실행
./deploy.sh
```

**출력 예시**:

```
╔═══════════════════════════════════════╗
║   Aegis-Link 배포 스크립트 v1.0      ║
╚═══════════════════════════════════════╝

[INFO] 환경 변수 파일 확인 중...
[INFO] 필수 환경 변수 확인 중...
[INFO] 보안 설정 적용 중...
[INFO] Docker 상태 확인 중...
[INFO] Docker 이미지 빌드 중... (최대 5분 소요)
...
[INFO] 서비스가 정상적으로 시작되었습니다!

╔═══════════════════════════════════════╗
║        배포 완료!                     ║
╚═══════════════════════════════════════╝

[INFO] 로컬 접속 주소: http://localhost
```

#### Step 4: 동작 확인

```bash
# 1. 브라우저에서 접속
open http://localhost

# 2. URL 분석 테스트
# - URL 입력창에 "https://google.com" 입력
# - 분석 시작 버튼 클릭
# - 실시간 분석 진행 상황 확인
```

---

### 외부 접속 (선택 사항)

팀원과 공유하거나 외부에서 테스트하려면:

```bash
# 1. cloudflared 설치
brew install cloudflare/cloudflare/cloudflared

# 2. Tunnel 실행
cloudflared tunnel --url http://localhost:80

# 3. 출력된 URL 공유
# 예: https://winter-cloud-1234.trycloudflare.com
```

**주의**: Tunnel 실행 중에는 전 세계 누구나 접속 가능하므로, 테스트 완료 후 `Ctrl+C`로 종료하세요.

---

## 🔧 서비스 포트

| 서비스    | 포트 | 설명                           | Docker 서비스명 |
| --------- | ---- | ------------------------------ | --------------- |
| backend   | 8000 | Rust API 서버                  | `api`           |
| react-ai  | 8001 | Python AI 분석 서버            | `ai`            |
| frontend  | 3001 | Next.js 프론트엔드             | `frontend`      |
| postgres  | 5432 | PostgreSQL 데이터베이스        | `postgres`      |
| search-ai | -    | 크롤러 (포트 없음, 백그라운드) | `search-ai`     |

---

## 📝 기술 스택

| 레이어          | 기술                                      |
| --------------- | ----------------------------------------- |
| **Backend**     | Rust, Axum, SeaORM, Vespera, Tower-HTTP   |
| **Frontend**    | Next.js 16 (App Router), TypeScript       |
| **AI Analysis** | Python, FastAPI, Claude API (Anthropic)   |
| **Crawler**     | Python, httpx, BeautifulSoup4, tldextract |
| **Database**    | PostgreSQL 16                             |
| **DevOps**      | Docker, Docker Compose                    |

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

## 🗄️ 데이터베이스

### 위치

- **호스트**: Docker 컨테이너 `aegis-link-postgres-1`
- **외부 포트**: `localhost:5432`
- **내부 포트**: `postgres:5432` (Docker 네트워크)

### 접속 정보

| 항목     | 값                           |
| -------- | ---------------------------- |
| Database | `aegis_link_db`              |
| User     | `aegis_user`                 |
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

## 📄 라이선스

MIT
