"""
===========================================
📄 main.py - FastAPI 서버 메인 진입점
===========================================
이 파일은 FastAPI 애플리케이션의 시작점입니다.
API 엔드포인트를 정의하고, 서버 시작/종료시 필요한 작업을 처리합니다.

FastAPI란?
- Python으로 API 서버를 쉽게 만들 수 있게 해주는 웹 프레임워크
- 자동으로 API 문서(Swagger UI)를 생성해줍니다
- 비동기(async/await) 처리를 지원하여 많은 요청을 동시에 처리할 수 있습니다
"""

import logging  # 로그 기록용
from contextlib import asynccontextmanager  # 서버 시작/종료 이벤트 처리용

from fastapi import FastAPI, HTTPException  # 웹 프레임워크와 에러 처리
from fastapi.middleware.cors import CORSMiddleware  # 다른 도메인에서 API 호출 허용

# 우리가 만든 모듈들 불러오기
from app.config import SERVER_HOST, SERVER_PORT  # 서버 설정
from app.models import AnalyzeRequest, AnalyzeResponse  # 요청/응답 스키마
from app.services.analyzer import analyze_url  # 메인 분석 함수
from app.services.whitelist import load_whitelist  # 화이트리스트 로드

# ============================================
# 로깅 설정
# ============================================
# 로그 형식: 시간 - 모듈명 - 레벨 - 메시지
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# 애플리케이션 생명주기 관리
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 시작/종료시 실행되는 함수
    
    - 시작시: 화이트리스트를 메모리에 로드
    - 종료시: 정리 작업 수행
    
    yield 전: 서버 시작 전 실행
    yield 후: 서버 종료 후 실행
    """
    # ===== 서버 시작시 =====
    logger.info("🚀 AI 분석 서버 시작 중...")
    
    # 화이트리스트(신뢰 도메인 목록)를 메모리에 미리 로드
    # 이렇게 하면 매 요청마다 파일을 읽지 않아도 됨
    whitelist = load_whitelist()
    logger.info(f"✅ 화이트리스트 로드 완료: {len(whitelist)}개 도메인")
    
    yield  # 여기서 서버가 실행되고 요청을 처리함
    
    # ===== 서버 종료시 =====
    logger.info("👋 AI 분석 서버 종료 중...")


# ============================================
# FastAPI 앱 생성
# ============================================
app = FastAPI(
    title="🛡️ Intelligent Scam Detection API",  # API 제목
    description="AI 기반 URL 분석으로 피싱 및 스캠 사이트를 탐지합니다",  # 설명
    version="1.0.0",  # 버전
    lifespan=lifespan  # 위에서 정의한 생명주기 함수 연결
)

# ============================================
# CORS 미들웨어 설정
# ============================================
# CORS: 다른 도메인(예: 프론트엔드)에서 이 API를 호출할 수 있게 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 접근 허용 (프로덕션에서는 제한 필요)
    allow_credentials=True,  # 쿠키/인증정보 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)


# ============================================
# 엔드포인트 정의
# ============================================

@app.get("/")
async def root():
    """
    루트 엔드포인트 - 서버 상태 확인용
    
    GET / 요청시 서버가 정상 동작중인지 확인할 수 있습니다.
    """
    return {
        "status": "healthy",
        "service": "Intelligent Scam Detection API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    상세 헬스체크 엔드포인트
    
    GET /health 요청시 각 컴포넌트의 상태를 확인할 수 있습니다.
    """
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "whitelist": "loaded"
        }
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    🎯 URL 분석 메인 엔드포인트
    
    POST /analyze 요청을 받아 5단계 분석 파이프라인을 실행합니다.
    
    분석 단계:
    - Phase 0: 화이트리스트 필터링 (신뢰 도메인 즉시 통과)
    - Phase 1: 리다이렉트 추적 (다중 리다이렉트 감지)
    - Phase 2: 도메인 메타데이터 (생성일, TLD 검사)
    - Phase 3: Claude AI 시맨틱 분석 (콘텐츠 분석)
    - Phase 4: 검색 엔진 교차 검증 (사칭 여부 확인)
    
    Args:
        request: URL과 request_id를 담은 요청 객체
        
    Returns:
        AnalyzeResponse: 분석 결과 (status, risk_score, reasons 등)
        
    Raises:
        HTTPException: 분석 중 오류 발생시 500 에러 반환
    """
    try:
        # 요청 수신 로그
        logger.info(f"📥 분석 요청 수신: {request.request_id}")
        
        # 메인 분석 함수 호출 (Phase 0~4 실행)
        result = await analyze_url(request)
        
        # 분석 완료 로그
        logger.info(f"📤 분석 완료: {request.request_id} → {result.status} ({result.risk_score}점)")
        
        return result
        
    except Exception as e:
        # 예외 발생시 에러 로그 기록 후 500 에러 반환
        logger.error(f"❌ 분석 실패 [{request.request_id}]: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"분석 중 오류 발생: {str(e)}"
        )


# ============================================
# 직접 실행시 서버 시작
# ============================================
if __name__ == "__main__":
    import uvicorn  # ASGI 서버
    
    # uvicorn으로 서버 실행
    # reload=True: 코드 변경시 자동 재시작 (개발 모드)
    uvicorn.run(
        "app.main:app",  # 실행할 앱 경로
        host=SERVER_HOST,  # 호스트 (기본: 0.0.0.0)
        port=SERVER_PORT,  # 포트 (기본: 8000)
        reload=True  # 자동 재시작 활성화
    )
