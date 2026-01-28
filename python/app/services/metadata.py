"""
===========================================
📄 metadata.py - Phase 2: 도메인 메타데이터 분석
===========================================
이 파일은 분석 파이프라인의 세 번째 단계(Phase 2)를 담당합니다.

도메인 메타데이터란?
- 도메인이 언제 등록되었는지 (생성일)
- 어떤 TLD(최상위 도메인)를 사용하는지

왜 메타데이터를 분석하는가?
1. 신규 도메인: 피싱 사이트는 대부분 최근에 만들어짐
2. 수상한 TLD: .xyz, .top 같은 저가 도메인은 피싱에 자주 악용

점수 체계:
- 14일 이내 생성된 도메인: +15점
- 수상한 TLD (.xyz, .top 등): +10점
"""

import whois  # WHOIS 조회 라이브러리
import logging  # 로그 기록용
from datetime import datetime, timezone  # 날짜 시간 처리
from typing import Optional  # 타입 힌트용

from app.config import (
    NEW_DOMAIN_DAYS_THRESHOLD,  # 신규 도메인 기준 (14일)
    NEW_DOMAIN_SCORE,           # 신규 도메인 점수 (+15)
    SUSPICIOUS_TLD_SCORE,       # 수상한 TLD 점수 (+10)
    SUSPICIOUS_TLDS             # 수상한 TLD 목록
)
from app.models import PhaseResult  # Phase 결과 모델
from app.utils.domain import extract_apex_domain, extract_tld  # 도메인 유틸

logger = logging.getLogger(__name__)


def analyze_metadata(url: str) -> PhaseResult:
    """
    도메인의 메타데이터(생성일, TLD)를 분석하여 위험도를 평가합니다.
    
    Args:
        url: 분석할 URL
        
    Returns:
        PhaseResult: Phase 2 분석 결과 (점수, 사유 등)
        
    동작 원리:
    1. URL에서 apex 도메인 추출 (예: example.xyz)
    2. WHOIS로 도메인 생성일 조회
    3. 생성일이 14일 이내면 +15점
    4. TLD가 수상한 목록에 있으면 +10점
    
    WHOIS란?
    - 도메인 등록 정보를 조회하는 프로토콜
    - 누가, 언제 도메인을 등록했는지 알 수 있음
    """
    score = 0  # 이 Phase의 총 점수
    reasons = []  # 점수 부여 사유들
    metadata = {}  # 추가 정보 저장
    
    # URL에서 도메인 정보 추출
    apex_domain = extract_apex_domain(url)  # 예: example.xyz
    tld = extract_tld(url)  # 예: xyz
    
    metadata["apex_domain"] = apex_domain
    metadata["tld"] = tld
    
    # ============================================
    # WHOIS 조회: 도메인 생성일 확인
    # ============================================
    try:
        # WHOIS 정보 조회
        domain_info = whois.whois(apex_domain)
        
        # 생성일 가져오기
        creation_date = domain_info.creation_date
        
        # 일부 레지스트라는 리스트로 반환하므로 첫 번째 값 사용
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        
        if creation_date:
            # ============================================
            # 시간대(timezone) 처리
            # ============================================
            # creation_date에 시간대 정보가 없으면 UTC로 설정
            if creation_date.tzinfo is None:
                creation_date = creation_date.replace(tzinfo=timezone.utc)
            
            # 현재 시간 (UTC 기준)
            now = datetime.now(timezone.utc)
            
            # 도메인 나이 계산 (일 단위)
            domain_age_days = (now - creation_date).days
            
            metadata["creation_date"] = creation_date.isoformat()
            metadata["domain_age_days"] = domain_age_days
            
            # 14일 이내 생성된 도메인이면 점수 부여
            if domain_age_days <= NEW_DOMAIN_DAYS_THRESHOLD:
                score += NEW_DOMAIN_SCORE
                reasons.append(f"신규 도메인 ({domain_age_days}일 전 생성) (+{NEW_DOMAIN_SCORE})")
                
    except Exception as e:
        # ============================================
        # WHOIS 조회 실패 처리
        # ============================================
        # WHOIS 실패는 흔한 일 (일부 도메인은 정보 비공개)
        # 명세서 원칙: 오류시 0점 처리하고 계속 진행
        logger.warning(f"⚠️ WHOIS 조회 실패 [{apex_domain}]: {e}")
        metadata["whois_error"] = str(e)
    
    # ============================================
    # TLD 검사: 수상한 최상위 도메인인지 확인
    # ============================================
    # TLD에서 마지막 부분만 추출 (예: co.kr → kr)
    tld_parts = tld.split(".")
    primary_tld = tld_parts[-1].lower() if tld_parts else ""
    
    # 수상한 TLD 목록과 비교
    if primary_tld in SUSPICIOUS_TLDS:
        score += SUSPICIOUS_TLD_SCORE
        reasons.append(f"수상한 TLD: .{primary_tld} (+{SUSPICIOUS_TLD_SCORE})")
        metadata["suspicious_tld"] = True
    else:
        metadata["suspicious_tld"] = False
    
    return PhaseResult(
        phase="Phase 2: Metadata",
        score=score,
        reasons=reasons,
        should_block=False,  # 이 단계에서는 즉시 차단하지 않음
        skip_remaining=False,  # 다음 Phase 계속 진행
        metadata=metadata
    )
