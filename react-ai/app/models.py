"""
===========================================
📄 models.py - 데이터 스키마 정의
===========================================
이 파일은 API 요청/응답 및 내부 데이터의 구조를 정의합니다.
Pydantic을 사용하여 데이터 유효성 검사와 타입 체크를 수행합니다.

Pydantic이란?
- Python에서 데이터 검증을 쉽게 해주는 라이브러리
- JSON 데이터를 Python 객체로 변환할 때 자동으로 타입 체크
- FastAPI와 함께 사용하면 API 문서도 자동 생성
"""

from typing import List, Literal  # 타입 힌트용
from pydantic import BaseModel, Field  # 데이터 모델 정의용


# ============================================
# API 요청 모델 (Rust 서버 → Python 서버)
# ============================================
class AnalyzeRequest(BaseModel):
    """
    URL 분석 요청 모델
    
    Rust 서버가 Python 서버에 분석을 요청할 때 보내는 데이터 형식
    """
    # url: 분석할 URL 주소 (필수값, "..."은 필수를 의미)
    url: str = Field(..., description="분석할 URL")
    
    # request_id: 요청 추적용 고유 ID (로그에서 어떤 요청인지 구분용)
    request_id: str = Field(..., description="요청 추적용 고유 ID")


# ============================================
# API 응답 모델 (Python 서버 → Rust 서버)
# ============================================
class AnalyzeResponse(BaseModel):
    """
    URL 분석 응답 모델
    
    Python 서버가 분석 결과를 Rust 서버에 반환할 때 사용하는 형식
    """
    # url: 분석한 URL (요청받은 URL을 그대로 반환)
    url: str = Field(..., description="분석된 URL")
    
    # status: 최종 판정 결과
    # - "SAFE": 안전 (0~29점)
    # - "WARNING": 주의 (30~59점)  
    # - "BLOCK": 차단 (60점 이상)
    # - "DEAD": 접속 불가 (서버 다운, 도메인 만료 등)
    # - "ERROR": 시스템 오류 (Claude API 장애, 네트워크 오류 등)
    status: Literal["SAFE", "WARNING", "BLOCK", "DEAD", "ERROR"] = Field(..., description="위험 상태")
    
    # risk_score: 총 위험 점수 (0점 이상)
    risk_score: int = Field(..., ge=0, description="총 위험 점수")
    
    # category: 콘텐츠 카테고리
    # - "Common": 일반 서비스 (금융, 쇼핑 등)
    # - "Negative": 불법 콘텐츠 (도박, 음란물 등)
    # - "Trusted": 화이트리스트 도메인
    # - "SystemError": 시스템 오류
    category: str = Field(default="", description="콘텐츠 카테고리")
    
    # keyword: AI가 감지한 브랜드/서비스명 (예: "신한은행", "네이버")
    keyword: str = Field(default="", description="감지된 브랜드/키워드")
    
    # reasons: 각 Phase에서 발생한 점수의 근거 목록
    # 예: ["New domain (+15)", "Suspicious TLD (+10)"]
    reasons: List[str] = Field(default_factory=list, description="점수 부여 사유 목록")
    
    # ===== 에러 정보 필드 (status="ERROR"일 때 사용) =====
    # error_code: 에러 코드 (AI_PROVIDER_OVERLOAD, AI_RATE_LIMIT_REACHED 등)
    error_code: str | None = Field(default=None, description="에러 코드")
    
    # error_message: 사용자에게 표시할 에러 메시지
    error_message: str | None = Field(default=None, description="사용자용 에러 메시지")
    
    # retry_after: 재시도 권장 시간 (초)
    retry_after: int | None = Field(default=None, description="재시도 권장 시간(초)")


# ============================================
# AI 분석 결과 모델 (내부용)
# ============================================
class AIAnalysisResult(BaseModel):
    """
    Claude AI 분석 결과 모델
    
    Phase 3에서 Claude API가 반환하는 JSON을 파싱한 결과
    """
    # keyword: 페이지가 사칭하려는 브랜드명
    keyword: str = Field(default="", description="감지된 브랜드명")
    
    # risk_score: AI가 판단한 위험도 (0.0 = 안전, 1.0 = 매우 위험)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="AI 위험도 평가")
    
    # category: 콘텐츠 분류
    # - "Common": 일반 서비스 → Phase 4 실행
    # - "Negative": 불법 콘텐츠 → 즉시 차단
    category: Literal["Common", "Negative"] = Field(default="Common", description="콘텐츠 카테고리")
    
    # description: AI가 위험하다고 판단한 구체적 근거
    description: str = Field(default="", description="위험 판단 근거")


# ============================================
# Phase 결과 모델 (내부용)
# ============================================
class PhaseResult(BaseModel):
    """
    각 Phase(단계)의 분석 결과 모델
    
    Phase 0~4 각각의 분석 결과를 표준화된 형식으로 저장
    """
    # phase: 어떤 단계인지 (예: "Phase 1: Redirect")
    phase: str = Field(..., description="분석 단계명")
    
    # score: 이 단계에서 부여된 점수
    score: int = Field(default=0, description="이 단계의 점수")
    
    # reasons: 점수 부여 사유 목록
    reasons: List[str] = Field(default_factory=list, description="점수 사유")
    
    # should_block: True면 남은 단계 건너뛰고 즉시 차단
    should_block: bool = Field(default=False, description="즉시 차단 여부")
    
    # skip_remaining: True면 남은 모든 단계 건너뜀 (화이트리스트 등)
    skip_remaining: bool = Field(default=False, description="남은 단계 건너뛰기")
    
    # metadata: 추가 정보 저장용 딕셔너리
    metadata: dict = Field(default_factory=dict, description="추가 메타데이터")
