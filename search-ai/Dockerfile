# =========================================
# Search-AI Dockerfile
# 지능형 도메인 홉 크롤러
# =========================================
# Multi-stage 빌드로 이미지 크기 최적화

# ---- Builder Stage ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# 의존성 파일 복사
COPY pyproject.toml ./

# 의존성 설치 (가상환경 없이)
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# 소스 코드 복사
COPY . .

# ---- Runtime Stage ----
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv 복사
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 애플리케이션 파일 복사
COPY --from=builder /app /app

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 환경 변수 기본값
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REACT_AI_URL=http://ai:8001 \
    BACKEND_URL=http://api:8000 \
    SEEDS_DIR=/app/seeds \
    MAX_URLS=500

# 실행
CMD ["uv", "run", "python", "main.py"]
