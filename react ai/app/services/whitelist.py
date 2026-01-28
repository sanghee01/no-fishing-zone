"""
===========================================
📄 whitelist.py - Phase 0: 화이트리스트 필터링
===========================================
이 파일은 분석 파이프라인의 첫 번째 단계(Phase 0)를 담당합니다.

화이트리스트란?
- 미리 "안전하다"고 확인된 도메인 목록 (예: google.com, naver.com)
- 이 목록에 있는 도메인은 분석 없이 바로 SAFE 판정

왜 화이트리스트가 필요한가?
1. 속도 향상: 유명 사이트는 분석할 필요 없음
2. 비용 절감: Claude API 호출 횟수 감소
3. 정확성: 구글, 네이버 같은 정상 사이트를 오탐하지 않음
"""

import logging  # 로그 기록용
from pathlib import Path  # 파일 경로 처리용
from typing import Set, Optional  # 타입 힌트용

from app.config import DATA_DIR  # 데이터 디렉토리 경로
from app.models import PhaseResult  # Phase 결과 모델
from app.utils.domain import extract_apex_domain  # 도메인 추출 함수

logger = logging.getLogger(__name__)

# ============================================
# 전역 변수: 화이트리스트 세트
# ============================================
# 서버 시작시 한 번만 로드하고, 이후에는 메모리에서 재사용
# Optional[Set[str]]: Set[str] 타입이거나 None일 수 있다는 의미
_whitelist: Optional[Set[str]] = None


def load_whitelist() -> Set[str]:
    """
    화이트리스트 파일을 읽어서 메모리에 로드합니다.
    
    이 함수는 서버 시작시 한 번 호출되며,
    이후에는 메모리에 캐시된 목록을 반환합니다.
    
    Returns:
        Set[str]: 화이트리스트 도메인 집합
        
    동작 원리:
    1. _whitelist가 이미 로드되어 있으면 그대로 반환 (캐싱)
    2. 처음 호출시 data/whitelist.txt 파일을 읽음
    3. 각 줄에서 도메인을 읽어 Set에 추가
    4. #으로 시작하는 줄은 주석으로 무시
    """
    global _whitelist  # 전역 변수 사용 선언
    
    # 이미 로드되어 있으면 캐시된 값 반환
    if _whitelist is not None:
        return _whitelist
    
    # 화이트리스트 파일 경로
    whitelist_path = DATA_DIR / "whitelist.txt"
    
    # 빈 Set으로 초기화
    _whitelist = set()
    
    try:
        # 파일이 존재하는지 확인
        if whitelist_path.exists():
            # 파일 열기 (UTF-8 인코딩)
            with open(whitelist_path, "r", encoding="utf-8") as f:
                # 각 줄을 순회
                for line in f:
                    # 앞뒤 공백 제거하고 소문자로 변환
                    domain = line.strip().lower()
                    
                    # 빈 줄이 아니고, 주석(#)으로 시작하지 않으면 추가
                    if domain and not domain.startswith("#"):
                        _whitelist.add(domain)
            
            logger.info(f"화이트리스트 로드: {len(_whitelist)}개 도메인")
        else:
            logger.warning(f"화이트리스트 파일 없음: {whitelist_path}")
            
    except Exception as e:
        logger.error(f"화이트리스트 로드 실패: {e}")
    
    return _whitelist


def check_whitelist(url: str) -> PhaseResult:
    """
    URL이 화이트리스트에 있는지 검사합니다.
    
    Args:
        url: 검사할 URL (예: "https://www.google.com/search?q=hello")
        
    Returns:
        PhaseResult: Phase 0 분석 결과
        - 화이트리스트에 있으면: skip_remaining=True (나머지 Phase 건너뜀)
        - 없으면: skip_remaining=False (다음 Phase 계속 진행)
        
    동작 원리:
    1. URL에서 apex 도메인 추출 (예: google.com)
    2. 화이트리스트에 해당 도메인이 있는지 확인
    3. 있으면 SAFE로 판정하고 남은 Phase 건너뜀
    """
    # 화이트리스트 가져오기 (이미 로드되어 있으면 캐시에서)
    whitelist = load_whitelist()
    
    # URL에서 apex 도메인 추출
    # 예: https://www.mail.google.com/inbox → google.com
    apex_domain = extract_apex_domain(url).lower()
    
    # 화이트리스트에 있는지 확인
    if apex_domain in whitelist:
        # ✅ 화이트리스트에 있음 = 신뢰 도메인
        return PhaseResult(
            phase="Phase 0: Whitelist",
            score=0,  # 점수 없음
            reasons=[f"신뢰 도메인: {apex_domain}"],
            should_block=False,  # 차단 아님
            skip_remaining=True,  # 🔥 핵심: 나머지 Phase 건너뜀
            metadata={"whitelisted": True, "apex_domain": apex_domain}
        )
    
    # ❌ 화이트리스트에 없음 = 다음 Phase 진행
    return PhaseResult(
        phase="Phase 0: Whitelist",
        score=0,
        reasons=[],  # 특별한 사유 없음
        should_block=False,
        skip_remaining=False,  # 다음 Phase 계속 진행
        metadata={"whitelisted": False, "apex_domain": apex_domain}
    )
