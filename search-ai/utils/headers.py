"""
===========================================
📄 headers.py - User-Agent 로테이션
===========================================
봇 차단을 회피하기 위해 요청마다 다른 User-Agent를 사용합니다.
"""

import random
from fake_useragent import UserAgent

# UserAgent 인스턴스 (캐시됨)
_ua = UserAgent()

# 백업용 하드코딩 User-Agent 목록
_FALLBACK_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    """
    랜덤한 User-Agent 문자열을 반환합니다.
    
    fake-useragent 라이브러리를 우선 사용하고,
    실패 시 하드코딩된 목록에서 선택합니다.
    
    Returns:
        User-Agent 문자열
    """
    try:
        return _ua.random
    except Exception:
        return random.choice(_FALLBACK_AGENTS)


def get_request_headers() -> dict[str, str]:
    """
    HTTP 요청에 사용할 헤더 딕셔너리를 반환합니다.
    
    포함 헤더:
    - User-Agent (랜덤)
    - Accept
    - Accept-Language
    - Accept-Encoding
    - Connection
    
    Returns:
        HTTP 헤더 딕셔너리
    """
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
