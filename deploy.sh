#!/bin/bash
set -euo pipefail  # 에러 발생 시 즉시 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 배너
echo "╔═══════════════════════════════════════╗"
echo "║   Aegis-Link 배포 스크립트 v1.0          ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# 1. 환경 변수 파일 확인
log_info "환경 변수 파일 확인 중..."
if [ ! -f .env ]; then
    log_error ".env 파일이 없습니다."
    log_info "다음 명령어로 템플릿을 복사하세요:"
    echo "  cp .env.example .env"
    echo "  # .env 파일을 열어서 API 키 등을 설정하세요"
    exit 1
fi

# 2. 필수 환경 변수 확인
log_info "필수 환경 변수 확인 중..."
source .env

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    log_error "ANTHROPIC_API_KEY가 설정되지 않았습니다."
    exit 1
fi

if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    log_warn "POSTGRES_PASSWORD가 설정되지 않았습니다. 기본값 'changeme' 사용"
fi

# 3. 파일 권한 설정
log_info "보안 설정 적용 중..."
chmod 600 .env
log_info ".env 파일 권한: $(ls -l .env | awk '{print $1}')"

# 4. Docker 실행 확인
log_info "Docker 상태 확인 중..."
if ! docker info > /dev/null 2>&1; then
    log_error "Docker가 실행되지 않았습니다."
    log_info "Docker Desktop을 실행한 후 다시 시도하세요."
    exit 1
fi

# 5. 기존 컨테이너 정리 (선택)
read -p "기존 컨테이너를 정리하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "기존 컨테이너 정리 중..."
    docker compose down -v
fi

# 6. Docker 이미지 빌드
log_info "Docker 이미지 빌드 중... (최대 5분 소요)"
docker compose build

# 7. 서비스 실행
log_info "서비스 실행 중..."
docker compose up -d

# 8. Health Check 대기
log_info "서비스 시작 대기 중... (최대 30초)"
for i in {1..30}; do
    if curl -s http://localhost/health/ > /dev/null 2>&1; then
        log_info "서비스가 정상적으로 시작되었습니다!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        log_error "서비스 시작 시간 초과"
        log_info "로그를 확인하세요: docker compose logs"
        exit 1
    fi
    
    echo -n "."
    sleep 1
done
echo ""

# 9. 서비스 상태 확인
log_info "서비스 상태:"
docker compose ps

# 10. 리소스 사용량 확인
log_info "리소스 사용량:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 11. 접속 정보 출력
echo ""
echo "╔═══════════════════════════════════════╗"
echo "║        배포 완료!                       ║"
echo "╚═══════════════════════════════════════╝"
echo ""
log_info "로컬 접속 주소: http://localhost"
log_info "Health Check: http://localhost/health/"
echo ""
log_warn "외부 접속을 위해 Cloudflare Tunnel을 실행하세요:"
echo "  cloudflared tunnel --url http://localhost:80"
echo ""
