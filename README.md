# Aegis Link

URL 평판 관리 시스템 - 모노레포

## 🏗️ 프로젝트 구조

```
aegis-link/
├── docker-compose.yml    # 전체 서비스 오케스트레이션
├── .env                  # 환경변수 (Git 제외)
├── .env.example          # 환경변수 템플릿
├── backend/              # Rust API 서버
│   ├── Dockerfile
│   ├── src/
│   └── Cargo.toml
├── frontend/             # Next.js 프론트엔드 (예정)
│   └── Dockerfile
└── ai/                   # Python AI 서버 (예정)
    └── Dockerfile
```

---

## 🚀 빠른 시작

### 사전 준비

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 및 실행

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 POSTGRES_PASSWORD 설정
```

### 2. 서비스 실행

```bash
# 전체 서비스 실행
docker compose up -d

# 상태 확인
docker compose ps
```

### 3. API 확인

- **Health Check**: http://localhost:8000/health/
- **Swagger UI**: http://localhost:8000/docs
- **API 테스트**:

  ```bash
  # URL 평판 등록
  curl -X POST -H "Content-Type: application/json" \
    -d '{"url":"https://test.com","description":"Test site","score":50,"is_black":false}' \
    http://localhost:8000/url-reputations/

  # URL 평판 조회
  curl "http://localhost:8000/url-reputations/?url=https://test.com"
  ```

---

## 🔧 서비스 포트

| 서비스       | 포트       | 설명                    |
| :----------- | :--------- | :---------------------- |
| **backend**  | 8000       | Rust API 서버           |
| **postgres** | 5432       | PostgreSQL 데이터베이스 |
| **frontend** | 3000, 3001 | Next.js (예정)          |
| **ai**       | 8001       | Python AI 서버 (예정)   |
| **nginx**    | 80         | 리버스 프록시 (예정)    |

---

## 💻 개발 가이드

### 전체 시스템 실행

```bash
# 전체 서비스 실행
docker compose up -d

# 로그 확인
docker compose logs -f api

# 특정 서비스만 재시작
docker compose restart api
```

### Backend 개발

```bash
# 코드 수정 후 재빌드
docker compose build api
docker compose up -d api

# 테스트 실행
cd backend
cargo test
```

### 주요 설정 파일

| 파일                    | 설명                             |
| :---------------------- | :------------------------------- |
| `docker-compose.yml`    | 전체 시스템 오케스트레이션       |
| `.env`                  | 환경변수 (비밀번호 등, Git 제외) |
| `backend/Dockerfile`    | Rust API 서버 빌드 정의          |
| `backend/.dockerignore` | 빌드 최적화 (불필요한 파일 제외) |

---

## 📝 기술 스택

- **Backend**: Rust, Axum, SeaORM, Vespera
- **Database**: PostgreSQL 16
- **Deployment**: Docker, Docker Compose
- **Frontend**: Next.js (예정)
- **AI**: Python (예정)

---

## 📌 개발자 노트

- Backend는 **Rust Nightly** 환경에서 빌드됩니다 (`sea-orm` 2.0-rc 호환성)
- DB 마이그레이션은 서버 시작 시 자동 실행됩니다
- 환경변수는 `.env` 파일로 관리되며 Git에 포함되지 않습니다

---

## 📄 라이선스

MIT
