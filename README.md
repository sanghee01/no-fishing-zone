# Aegis Link

URL 평판 관리 시스템 - 모노레포

## 🏗️ 프로젝트 구조

```
aegis-link/
├── docker-compose.yml    # 전체 서비스 오케스트레이션
├── .env                  # 환경변수 (Git 제외)
├── .env.example          # 환경변수 템플릿
├── backend/              # Rust API 서버 (Axum + SeaORM)
│   ├── Dockerfile
│   ├── src/
│   └── Cargo.toml
├── frontend/             # Next.js 프론트엔드
│   ├── app/
│   ├── lib/
│   └── package.json
└── ai/                   # Python AI 서버 (예정)
    └── Dockerfile
```

---

## 🚀 빠른 시작

### 사전 준비

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 및 실행
- [Node.js](https://nodejs.org/) (v18 이상) - 프론트엔드 로컬 실행 시

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 POSTGRES_PASSWORD 설정
```

### 2. 백엔드 및 DB 실행

```bash
# 전체 서비스 실행 (Docker)
docker compose up -d

# 상태 확인
docker compose ps
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

- 접속 주소: [http://localhost:3000](http://localhost:3000)

---

## 🔧 서비스 포트

| 서비스       | 포트 | 설명                    |
| :----------- | :--- | :---------------------- |
| **backend**  | 8000 | Rust API 서버           |
| **frontend** | 3000 | Next.js 프론트엔드      |
| **postgres** | 5432 | PostgreSQL 데이터베이스 |
| **ai**       | 8001 | Python AI 서버 (예정)   |

---

## 💻 개발 가이드

### 백엔드 (Rust)

- **CORS 설정**: 프론트엔드와의 통신을 위해 `tower-http`를 이용한 Permissive CORS가 설정되어 있습니다.
- **API 로그**: `println!`을 통해 요청 URL 및 DB 조회 성공 여부를 터미널에서 실시간으로 확인할 수 있습니다.
- **404 처리**: DB에 정보가 없는 경우 `404 Not Found`를 반환합니다.

### 프론트엔드 (Next.js)

- **API 연동**: `@devup-api/fetch`를 사용하여 타입 안전한 API 호출을 구현했습니다.
- **예외 처리**: 백엔드에서 404 응답을 보낼 경우, 단순 에러가 아닌 "평판 정보가 아직 등록되지 않았습니다"라는 안내 UI를 표시합니다.

### 데이터베이스 직접 조작 (도커)

백엔드 서버가 도커 컨테이너에서 실행 중일 때, 데이터베이스에 수동으로 데이터를 넣는 방법입니다:

```bash
docker exec -it aegis-link-postgres-1 psql -U aegis_user -d aegis_link_db -c "INSERT INTO url_reputations (url, description, score, is_black) VALUES ('https://example.com', '테스트용 안전한 사이트', 100, false);"
```

---

## 📝 기술 스택

- **Backend**: Rust, Axum, SeaORM, Vespera, Tower-HTTP (CORS)
- **Frontend**: Next.js 15 (App Router), TypeScript, @devup-api/fetch
- **Database**: PostgreSQL 16
- **Deployment**: Docker, Docker Compose

---

## 📌 개발자 노트

- Backend는 **Rust Nightly** 환경에서 빌드됩니다.
- 프론트엔드에서 API 주소는 `NEXT_PUBLIC_API_BASE_URL` 환경변수로 설정 가능하며, 기본값은 `http://localhost:8000/`입니다.
- DB 마이그레이션은 서버 시작 시 자동 실행됩니다.

---

## 📄 라이선스

MIT
