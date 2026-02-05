# =========================================
# Search-AI Dockerfile - Final Evolution v2
# Playwright 클러스터 크롤러
# =========================================
# Python 3.13 + Playwright 수동 설치

FROM python:3.13-slim-bookworm

WORKDIR /app

# 시스템 패키지 설치 (Playwright 의존성)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libatspi2.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 파일 복사
COPY pyproject.toml ./

# 의존성 설치
RUN uv sync --no-dev

# ★ Playwright 브라우저 설치 (Chromium만)
RUN uv run playwright install chromium

# 소스 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 환경 변수 기본값
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REACT_AI_URL=http://ai:8001 \
    BACKEND_URL=http://api:8000 \
    SEEDS_DIR=/app/seeds \
    MAX_URLS=200 \
    NUM_WORKERS=3 \
    ENABLE_CERTSTREAM=true

# ★ 클러스터 워커로 무한 실행
CMD ["uv", "run", "python", "main.py"]
