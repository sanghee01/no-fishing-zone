"""
===========================================
📄 redirect.py - Phase 1: 리다이렉트 추적
===========================================
이 파일은 분석 파이프라인의 두 번째 단계(Phase 1)를 담당합니다.

리다이렉트란?
- URL A에 접속했는데 URL B로 자동 이동하는 것
- 예: bit.ly/xxx → 실제사이트.com

왜 리다이렉트를 추적하는가?
1. 피싱 사이트는 추적을 피하기 위해 여러 번 리다이렉트함
2. 무한 리다이렉트 루프로 서버 자원을 고갈시키려는 공격 탐지
3. 실제 최종 URL을 알아야 정확한 분석 가능

점수 체계:
- 리다이렉트 1회당 +5점
- 20회 초과시 즉시 BLOCK (무한 루프 의심)
"""

import httpx  # 비동기 HTTP 클라이언트
import logging  # 로그 기록용
from typing import Tuple, Optional  # 타입 힌트용

from app.config import (
    REDIRECT_SCORE_PER_HOP,  # 리다이렉트 1회당 점수 (+5)
    MAX_REDIRECT_HOPS,       # 최대 리다이렉트 허용 횟수 (20)
    REQUEST_TIMEOUT,         # 요청 타임아웃 (10초)
    USER_AGENT,              # 브라우저 위장용 User-Agent
    CONNECTION_FAILURE_SCORE # 접속 실패 시 추가 점수 (+15)
)
from app.models import PhaseResult  # Phase 결과 모델

logger = logging.getLogger(__name__)


async def track_redirects(url: str) -> Tuple[PhaseResult, str, Optional[str]]:
    """
    URL의 리다이렉트를 추적하고 위험도를 평가합니다.
    
    Args:
        url: 분석할 URL
        
    Returns:
        Tuple[PhaseResult, final_url, html_content]:
        - PhaseResult: Phase 1 분석 결과 (점수, 사유 등)
        - final_url: 리다이렉트 후 최종 URL
        - html_content: 최종 페이지의 HTML 내용 (Phase 3에서 사용)
        
    동작 원리:
    1. httpx 클라이언트로 URL에 접속
    2. 자동으로 모든 리다이렉트를 따라감
    3. response.history에서 리다이렉트 횟수 확인
    4. 횟수에 따라 점수 부여
    
    예외 처리:
    - 타임아웃: 0점 처리하고 계속 진행
    - 기타 에러: 0점 처리하고 계속 진행
    - 무한 루프: 100점 부여하고 즉시 BLOCK
    """
    try:
        # ============================================
        # HTTP 클라이언트 생성 및 요청
        # ============================================
        # async with: 요청 완료 후 자동으로 연결 정리
        async with httpx.AsyncClient(
            follow_redirects=True,  # 리다이렉트 자동 따라가기
            max_redirects=MAX_REDIRECT_HOPS + 1,  # 최대 허용 + 1 (초과 감지용)
            timeout=REQUEST_TIMEOUT,  # 타임아웃 설정
            verify=False,  # SSL 인증서 검증 무시 (자체 서명 등 접속 허용)
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }  # 브라우저로 위장 (헤더 단순화하여 호환성 확보)
        ) as client:
            # GET 요청 보내기
            response = await client.get(url)
            
            # ============================================
            # 리다이렉트 분석
            # ============================================
            # response.history: 거쳐온 리다이렉트 응답들의 리스트
            # 예: A → B → C면 history에 A, B 응답이 들어있음
            redirect_count = len(response.history)
            
            # 최종 URL (리다이렉트 끝난 후의 URL)
            final_url = str(response.url)
            
            # HTML 내용 (Phase 3 AI 분석에 사용)
            html_content = response.text
            
            # ============================================
            # 무한 루프 체크
            # ============================================
            if redirect_count > MAX_REDIRECT_HOPS:
                # 🚨 무한 루프 의심 - 즉시 차단
                return (
                    PhaseResult(
                        phase="Phase 1: Redirect",
                        score=100,  # 최고 점수 부여 = 무조건 BLOCK
                        reasons=[f"무한 리다이렉트 루프 감지 ({redirect_count}회)"],
                        should_block=True,  # 즉시 차단
                        skip_remaining=True,  # 나머지 Phase 건너뜀
                        metadata={
                            "redirect_count": redirect_count,
                            "final_url": final_url
                        }
                    ),
                    final_url,
                    None  # HTML 내용 없음 (차단이므로 불필요)
                )
            
            # ============================================
            # 정상 케이스: 점수 계산
            # ============================================
            # 리다이렉트 횟수 × 1회당 점수
            score = redirect_count * REDIRECT_SCORE_PER_HOP
            reasons = []
            
            # 리다이렉트가 있었으면 사유 추가
            if redirect_count > 0:
                reasons.append(f"리다이렉트 {redirect_count}회 (+{score})")
            
            return (
                PhaseResult(
                    phase="Phase 1: Redirect",
                    score=score,
                    reasons=reasons,
                    should_block=False,
                    skip_remaining=False,
                    metadata={
                        "redirect_count": redirect_count,
                        "final_url": final_url,
                        "status_code": response.status_code  # HTTP 상태코드 (200, 404 등)
                    }
                ),
                final_url,
                html_content
            )
            
    except httpx.TooManyRedirects:
        # ============================================
        # httpx가 자체적으로 감지한 과다 리다이렉트
        # ============================================
        return (
            PhaseResult(
                phase="Phase 1: Redirect",
                score=100,
                reasons=["리다이렉트 제한 초과 (강제 차단)"],
                should_block=True,
                skip_remaining=True,
                metadata={"error": "TooManyRedirects"}
            ),
            url,
            None
        )
        
    except httpx.TimeoutException:
        # ============================================
        # 타임아웃 발생 (서버 응답 없음) = 수상한 사이트 가능성
        # ============================================
        logger.warning(f"⏱️ 타임아웃: {url}")
        return (
            PhaseResult(
                phase="Phase 1: Redirect",
                score=CONNECTION_FAILURE_SCORE,  # 0 → 15 (Recall 개선)
                reasons=[f"접속 타임아웃 - 수상한 사이트 (+{CONNECTION_FAILURE_SCORE})"],
                should_block=False,
                skip_remaining=False,
                metadata={"error": "Timeout", "connection_failure": True}
            ),
            url,
            None
        )
        
    except Exception as e:
        # ============================================
        # 기타 예외 (네트워크 오류 등) = 수상한 사이트 가능성
        # ============================================
        logger.error(f"❌ 리다이렉트 추적 실패 [{url}]: {e}")
        return (
            PhaseResult(
                phase="Phase 1: Redirect",
                score=CONNECTION_FAILURE_SCORE,  # 0 → 15 (Recall 개선)
                reasons=[f"접속 실패 - 수상한 사이트 (+{CONNECTION_FAILURE_SCORE})"],
                should_block=False,
                skip_remaining=False,
                metadata={"error": str(e), "connection_failure": True}
            ),
            url,
            None
        )
