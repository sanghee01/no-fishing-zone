"""
===========================================
📄 domain.py - 도메인 처리 유틸리티
===========================================
이 파일은 URL에서 도메인 정보를 추출하는 유틸리티 함수들을 제공합니다.

주요 개념:
- URL: https://www.mail.google.com/inbox?id=123
- 호스트: www.mail.google.com
- Apex 도메인: google.com (루트 도메인)
- TLD: com (최상위 도메인)
- 서브도메인: www.mail

왜 Apex 도메인을 추출하는가?
- 화이트리스트 비교시 서브도메인은 무시
- www.google.com, mail.google.com, drive.google.com 모두 google.com

tldextract 라이브러리:
- URL에서 도메인 파트를 정확하게 분리
- .co.kr, .ac.jp 같은 복합 TLD도 올바르게 처리
"""

import tldextract  # URL 도메인 파싱 라이브러리
from urllib.parse import urlparse  # URL 파싱
import logging

logger = logging.getLogger(__name__)


def extract_apex_domain(url: str) -> str:
    """
    URL에서 Apex(루트) 도메인을 추출합니다.
    
    Args:
        url: 분석할 URL
        
    Returns:
        str: Apex 도메인 (예: google.com, example.co.kr)
        
    예시:
        https://www.shinhan.com/path → shinhan.com
        https://sub.domain.example.co.kr → example.co.kr
        https://www.mail.google.com → google.com
        
    tldextract 동작:
    - domain: 핵심 도메인명 (google, shinhan)
    - suffix: TLD (.com, .co.kr)
    - subdomain: 서브도메인 (www, mail)
    """
    try:
        # URL에서 도메인 파트 추출
        extracted = tldextract.extract(url)
        
        # suffix(TLD)가 있으면 domain.suffix 형태로 반환
        if extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        
        # TLD가 없으면 (localhost 같은 경우) domain만 반환
        return extracted.domain
        
    except Exception as e:
        logger.error(f"❌ 도메인 추출 실패 [{url}]: {e}")
        return ""


def extract_tld(url: str) -> str:
    """
    URL에서 최상위 도메인(TLD)을 추출합니다.
    
    Args:
        url: 분석할 URL
        
    Returns:
        str: TLD (예: com, xyz, co.kr)
        
    예시:
        https://example.xyz → xyz
        https://example.co.kr → co.kr
        https://example.com → com
        
    용도:
    - Phase 2에서 수상한 TLD (.xyz, .top 등) 검사
    """
    try:
        extracted = tldextract.extract(url)
        return extracted.suffix  # com, xyz, co.kr 등
        
    except Exception as e:
        logger.error(f"❌ TLD 추출 실패 [{url}]: {e}")
        return ""


def normalize_url(url: str) -> str:
    """
    URL을 정규화(표준 형태로 변환)합니다.
    
    Args:
        url: 원본 URL
        
    Returns:
        str: 정규화된 URL
        
    정규화 작업:
    1. 스킴(http://)이 없으면 https:// 추가
    2. 호스트명을 소문자로 변환
    3. 불필요한 부분 정리
    
    예시:
        google.com → https://google.com
        HTTP://GOOGLE.COM → https://google.com
    """
    try:
        # http:// 또는 https://로 시작하지 않으면 https:// 추가
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # URL 파싱
        parsed = urlparse(url)
        
        # 정규화된 URL 재구성
        # netloc: 호스트명 (소문자로 변환)
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}"
        
        # path가 있으면 추가
        if parsed.path:
            normalized += parsed.path
            
        # 쿼리 파라미터가 있으면 추가
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized
        
    except Exception as e:
        logger.error(f"❌ URL 정규화 실패 [{url}]: {e}")
        return url  # 실패시 원본 반환


def get_full_domain(url: str) -> str:
    """
    URL에서 전체 도메인(서브도메인 포함)을 추출합니다.
    
    Args:
        url: 분석할 URL
        
    Returns:
        str: 전체 도메인 (예: www.mail.google.com)
        
    extract_apex_domain과의 차이:
    - extract_apex_domain: google.com (루트만)
    - get_full_domain: www.mail.google.com (전체)
    
    용도:
    - 정확한 도메인 비교가 필요할 때
    - 서브도메인까지 표시해야 할 때
    """
    try:
        # 스킴이 없으면 추가 (urlparse가 제대로 파싱하도록)
        parsed = urlparse(url if "://" in url else f"https://{url}")
        return parsed.netloc.lower()  # 호스트 부분만 반환 (소문자)
        
    except Exception as e:
        logger.error(f"❌ 전체 도메인 추출 실패 [{url}]: {e}")
        return ""
