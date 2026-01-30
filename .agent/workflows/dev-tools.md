---
description: Vespertide 및 Vespera 관련 빌드, 테스트, CLI 명령어 실행 워크플로우
---

# 🛠 Dev Tools Workflow

이 워크플로우는 프로젝트의 데이터베이스 관리 및 API 개발을 위한 도구 세트입니다.

## 🗄 Vespertide (DB Schema & Migration)

### 1. 스키마 변경 사항 확인

// turbo

```bash
cargo run -p vespertide-cli -- diff
```

### 2. SQL 프리뷰 (마이그레이션 전 확인)

// turbo

```bash
cargo run -p vespertide-cli -- sql
```

### 3. 새 마이그레이션 생성

```bash
# 메시지를 입력하여 마이그레이션을 생성합니다.
cargo run -p vespertide-cli -- revision -m "YOUR_MESSAGE"
```

### 4. ORM 코드 내보내기 (SeaORM)

// turbo

```bash
cargo run -p vespertide-cli -- export --orm seaorm
```

---

## 🔍 Diagnostics & Health (인프라 진단)

### 1. 전체 서비스 상태 확인 (출석 체크)

// turbo

```bash
docker compose ps
```

### 2. 특정 서비스 실시간 보고서 (로그 확인)

```bash
# 서비스 이름을 입력하세요 (api, node, ai, nginx, postgres 등)
docker compose logs -f [SERVICE_NAME]
```

### 3. 서비스 생존 확인 (Health Check)

// turbo

```bash
# Nginx가 인식하는 각 서비스의 상태를 점검합니다.
docker compose exec nginx curl -s http://api:8000/health
docker compose exec nginx curl -s http://ai:8001/health
```

### 4. 전체 시스템 청소 (철거)

```bash
# 사용하지 않는 데이터까지 싹 정리합니다 (주의: DB 데이터 삭제됨)
docker compose down -v
```

---

## 🚀 Vespera (Web API & OpenAPI)

### 1. 테스트 실행

// turbo

```bash
cargo test --workspace
```

### 2. 로컬 서버 실행 (OpenAPI 확인용)

```bash
# 서버를 실행하고 http://localhost:3000/docs 에 접속하세요.
cargo run
```

### 3. JSON 스키마 재생성

// turbo

```bash
cargo run -p vespertide-schema-gen -- --out schemas
```
