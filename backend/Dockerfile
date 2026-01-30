# ============================================
# 1단계: 빌드 스테이지
# ============================================
# Rust 컴파일러가 포함된 공식 이미지 사용
FROM rustlang/rust:nightly AS builder

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일만 먼저 복사 (캐싱 최적화)
# Cargo.toml과 Cargo.lock이 변경되지 않으면 의존성을 다시 다운로드하지 않음
COPY Cargo.toml Cargo.lock ./

# 더미 main.rs를 만들어서 의존성만 먼저 빌드 (캐싱 전략)
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src target

# 실제 소스 코드 복사
COPY . .

# Release 모드로 빌드
RUN cargo build --release

# ============================================
# 2단계: 실행 스테이지
# ============================================
# 경량 Debian 이미지 사용 (Alpine보다 호환성 좋음)
FROM debian:bookworm-slim

# 필요한 런타임 라이브러리 설치
# - ca-certificates: HTTPS 통신용
# - libssl3: OpenSSL 라이브러리
# - wget: healthcheck용
RUN apt-get update && \
    apt-get install -y ca-certificates libssl3 wget && \
    rm -rf /var/lib/apt/lists/*

# 빌드 스테이지에서 컴파일된 실행 파일 및 설정 파일 복사
COPY --from=builder /app/target/release/aegis-link /usr/local/bin/aegis-link
COPY --from=builder /app/openapi.json /usr/local/bin/openapi.json
WORKDIR /usr/local/bin

# 8000번 포트 노출 (기존 docker-compose 설정과 맞춤)
EXPOSE 8000

# 환경변수 기본값 설정
ENV PORT=8000

# 컨테이너 시작 시 실행할 명령
CMD ["aegis-link"]
