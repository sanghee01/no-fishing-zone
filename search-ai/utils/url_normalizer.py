"""
===========================================
📄 url_normalizer.py - URL 정규화 유틸리티
===========================================
URL을 표준화하여 DB 중복을 방지합니다.

예시:
- http://example.com → https://example.com
- https://example.com/ → https://example.com
- https://www.example.com → https://example.com
"""

from urllib.parse import urlparse, urlunparse
import tldextract


def normalize_url(url: str) -> str:
    """
    URL을 정규화하여 일관된 형식으로 반환합니다.
    
    정규화 규칙:
    1. 스킴을 https로 통일
    2. www. 접두사 제거
    3. 후행 슬래시 제거
    4. 소문자로 변환
    5. 기본 포트(80, 443) 제거
    6. 프래그먼트(#...) 제거
    
    Args:
        url: 정규화할 URL 문자열
        
    Returns:
        정규화된 URL 문자열
    """
    if not url:
        return ""
    
    # URL 파싱
    parsed = urlparse(url.strip())
    
    # ★ 원본 스킴 유지 (http/https), 없으면 https 기본값
    scheme = parsed.scheme.lower() if parsed.scheme in ("http", "https") else "https"
    
    # 호스트 정규화 (소문자, www. 제거)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    # 기본 포트 제거
    if netloc.endswith(":80") or netloc.endswith(":443"):
        netloc = netloc.rsplit(":", 1)[0]
    
    # 경로에서 후행 슬래시 제거 (루트 경로 제외)
    path = parsed.path.rstrip("/") if parsed.path != "/" else ""
    
    # 쿼리는 유지, 프래그먼트는 제거
    query = parsed.query
    
    # URL 재조립
    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    
    return normalized


def extract_apex_domain(url: str) -> str:
    """
    URL에서 Apex 도메인(등록된 도메인)을 추출합니다.
    
    예시:
    - https://sub.example.co.kr/path → example.co.kr
    - https://www.google.com → google.com
    
    Args:
        url: 도메인을 추출할 URL
        
    Returns:
        Apex 도메인 문자열
    """
    extracted = tldextract.extract(url)
    return extracted.registered_domain or ""


def is_same_domain(url1: str, url2: str) -> bool:
    """
    두 URL이 동일한 Apex 도메인인지 확인합니다.
    
    Args:
        url1: 첫 번째 URL
        url2: 두 번째 URL
        
    Returns:
        동일 도메인이면 True
    """
    return extract_apex_domain(url1) == extract_apex_domain(url2)


def is_external_link(base_url: str, target_url: str) -> bool:
    """
    target_url이 base_url과 다른 Apex 도메인인지 확인합니다.
    (외부 링크 여부 판단)
    
    Args:
        base_url: 현재 페이지 URL
        target_url: 검사할 링크 URL
        
    Returns:
        외부 링크이면 True
    """
    return not is_same_domain(base_url, target_url)
