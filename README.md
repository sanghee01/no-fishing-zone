# Aegis Link

URL 평판 관리 시스템 - 모노레포

## 프로젝트 구조

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

## 빠른 시작

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 POSTGRES_PASSWORD 설정
```

### 2. Docker로 실행

```bash
# 전체 서비스 실행
docker compose up -d

# 특정 서비스만 실행
docker compose up -d postgres  # DB만
docker compose up api          # API만 (로그 확인)
```

### 3. API 확인

- Health Check: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs

## 서비스 포트

- **nginx**: 80 (리버스 프록시)
- **frontend**: 3000, 3001
- **backend**: 8000
- **ai**: 8001
- **postgres**: 5432

## 개발 가이드

### Backend (Rust)

```bash
cd backend
cargo run  # 로컬 실행
cargo test # 테스트
```

## 배포

```bash
# 프로덕션 빌드
docker compose build

# 서버에서 실행
docker compose up -d
```

## 라이선스

MIT
