"""
===========================================
📄 analyzer.py - 메인 분석 파이프라인 오케스트레이터
===========================================
이 파일은 Phase 0~4를 순차적으로 실행하고 최종 결과를 반환합니다.

오케스트레이터란?
- 여러 모듈(Phase)을 조율하여 전체 흐름을 관리하는 역할
- 마치 오케스트라 지휘자처럼 각 악기(Phase)를 조화롭게 연주

이 파일의 역할:
1. Phase 0 → 1 → 2 → 3 → 4 순서로 실행
2. 각 Phase의 점수를 합산
3. 총점에 따라 최종 상태(SAFE/WARNING/BLOCK) 결정
4. 예외 발생시 해당 Phase만 0점 처리하고 계속 진행
"""

import logging  # 로그 기록용
from typing import Tuple  # 타입 힌트용

from app.config import BLOCK_THRESHOLD, WARNING_THRESHOLD  # 임계값 (60, 30)
from app.models import AnalyzeRequest, AnalyzeResponse, PhaseResult
from app.services.whitelist import check_whitelist      # Phase 0
from app.services.redirect import track_redirects       # Phase 1
from app.services.metadata import analyze_metadata      # Phase 2
from app.services.ai_analyzer import analyze_with_ai, analyze_url_only  # Phase 3 + Fallback
from app.services.search_verifier import verify_with_search  # Phase 4

logger = logging.getLogger(__name__)


def determine_status(score: int) -> str:
    """
    총 위험 점수를 기반으로 최종 상태를 결정합니다.
    
    Args:
        score: 모든 Phase 점수의 합계
        
    Returns:
        str: "SAFE", "WARNING", 또는 "BLOCK"
        
    판정 기준:
    - 60점 이상: BLOCK (차단)
    - 30~59점: WARNING (경고)
    - 30점 미만: SAFE (안전)
    """
    if score >= BLOCK_THRESHOLD:
        return "BLOCK"
    elif score >= WARNING_THRESHOLD:
        return "WARNING"
    return "SAFE"


async def analyze_url(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    🎯 메인 분석 함수: URL을 5단계로 분석하여 위험도를 평가합니다.
    
    Args:
        request: 분석 요청 (url, request_id 포함)
        
    Returns:
        AnalyzeResponse: 분석 결과 (status, risk_score, reasons 등)
        
    분석 흐름:
    1. Phase 0: 화이트리스트 → 일치하면 즉시 SAFE 반환
    2. Phase 1: 리다이렉트 → 무한루프면 즉시 BLOCK 반환
    3. Phase 2: 메타데이터 → 도메인 나이/TLD 점수
    4. Phase 3: AI 분석 → Negative면 즉시 BLOCK 반환
    5. Phase 4: 검색 검증 → Common일 때만 실행
    6. 총점 계산 → 상태 결정
    
    예외 처리 원칙:
    - 각 Phase에서 오류 발생시 0점 처리
    - 오류로 인해 전체 분석이 중단되지 않음
    """
    url = request.url
    # URL 정규화: 끝의 슬래시 제거 (중복 캐싱 방지)
    # 예: https://drive.google.com/ → https://drive.google.com
    url = url.rstrip("/")
    total_score = 0  # 총 위험 점수
    all_reasons = []  # 모든 점수 사유
    category = ""  # AI가 판정한 카테고리
    keyword = ""  # AI가 추출한 브랜드명
    
    logger.info(f"🔍 [{request.request_id}] 분석 시작: {url}")
    
    # ============================================
    # Phase 0: 화이트리스트 검사
    # ============================================
    # 신뢰 도메인이면 나머지 Phase 건너뛰고 SAFE 반환
    try:
        phase0_result = check_whitelist(url)
        total_score += phase0_result.score
        all_reasons.extend(phase0_result.reasons)
        
        if phase0_result.skip_remaining:
            # 🟢 화이트리스트에 있음 = 즉시 SAFE
            logger.info(f"✅ [{request.request_id}] 화이트리스트 통과 - SAFE")
            return AnalyzeResponse(
                url=url,
                status="SAFE",
                risk_score=0,
                category="Trusted",
                keyword="",
                reasons=all_reasons
            )
    except Exception as e:
        logger.error(f"❌ [{request.request_id}] Phase 0 오류: {e}")
        all_reasons.append("Phase 0: 오류 발생 - 건너뜀")
    
    # ============================================
    # Phase 1: 리다이렉트 추적
    # ============================================
    # 페이지 접속하여 리다이렉트 추적 + HTML 다운로드
    html_content = None  # Phase 3에서 사용할 HTML
    final_url = url  # 리다이렉트 후 최종 URL
    
    try:
        phase1_result, final_url, html_content = await track_redirects(url)
        total_score += phase1_result.score
        all_reasons.extend(phase1_result.reasons)
        
        if phase1_result.should_block:
            # 🔴 무한 리다이렉트 = 즉시 BLOCK
            logger.warning(f"🚫 [{request.request_id}] 리다이렉트 루프 - BLOCK")
            return AnalyzeResponse(
                url=url,
                status="BLOCK",
                risk_score=100,
                category="Malicious",
                keyword="",
                reasons=all_reasons
            )
    except Exception as e:
        logger.error(f"❌ [{request.request_id}] Phase 1 오류: {e}")
        all_reasons.append(f"Phase 1: 오류 발생 ({str(e)}) - 건너뜀")
    
    # ============================================
    # Phase 2: 도메인 메타데이터 분석
    # ============================================
    # WHOIS로 도메인 나이 확인, TLD 검사
    try:
        phase2_result = analyze_metadata(final_url)
        total_score += phase2_result.score
        all_reasons.extend(phase2_result.reasons)
    except Exception as e:
        logger.error(f"❌ [{request.request_id}] Phase 2 오류: {e}")
        all_reasons.append(f"Phase 2: 오류 발생 ({str(e)}) - 건너뜀")
    
    # ============================================
    # Phase 3: AI 분석 (v4 - URL-Only Fallback 추가)
    # ============================================
    # HTML 내용을 AI가 분석하여 브랜드/위험도 추출
    # v4 개선: HTML 없으면 URL만으로 분석 (Recall 개선)
    try:
        if html_content:
            # HTML 있으면 정상 분석
            phase3_result = await analyze_with_ai(html_content)
        else:
            # HTML 없으면 URL-Only Fallback 분석
            logger.info(f"🔄 [{request.request_id}] HTML 없음 - URL-Only AI 분석 실행")
            phase3_result = await analyze_url_only(url)
        
        total_score += phase3_result.score
        all_reasons.extend(phase3_result.reasons)
        
        # AI 분석 결과에서 keyword와 category 추출
        keyword = phase3_result.metadata.get("keyword", "")
        category = phase3_result.metadata.get("category", "Common")
        
        if phase3_result.should_block:
            # 🔴 Negative 콘텐츠 (도박/음란물) = 즉시 BLOCK
            logger.warning(f"🚫 [{request.request_id}] Negative 콘텐츠 - BLOCK")
            return AnalyzeResponse(
                url=url,
                status="BLOCK",
                risk_score=total_score,
                category=category,
                keyword=keyword,
                reasons=all_reasons
            )
    except Exception as e:
        logger.error(f"❌ [{request.request_id}] Phase 3 오류: {e}")
        all_reasons.append(f"Phase 3: 오류 발생 ({str(e)}) - 건너뜀")
    
    # ============================================
    # Phase 4: 검색 엔진 교차 검증
    # ============================================
    # Common 카테고리일 때만 실행 (사칭 가능성이 있는 경우)
    if category == "Common" and keyword:
        try:
            phase4_result = await verify_with_search(final_url, keyword)
            total_score += phase4_result.score
            all_reasons.extend(phase4_result.reasons)
        except Exception as e:
            logger.error(f"❌ [{request.request_id}] Phase 4 오류: {e}")
            all_reasons.append(f"Phase 4: 오류 발생 ({str(e)}) - 건너뜀")
    
    # ============================================
    # 최종 판정
    # ============================================
    status = determine_status(total_score)
    
    logger.info(f"📊 [{request.request_id}] 분석 완료: {status} ({total_score}점)")
    
    return AnalyzeResponse(
        url=url,
        status=status,
        risk_score=total_score,
        category=category if category else "Unknown",
        keyword=keyword,
        reasons=all_reasons
    )
