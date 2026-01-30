"""
===========================================
📄 link_extractor.py - 링크 추출기
===========================================
HTML 페이지에서 링크를 추출하고 필터링합니다.
"""

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from utils.url_normalizer import normalize_url, extract_apex_domain, is_external_link
from utils.logging_config import get_logger

logger = get_logger()


def extract_links_from_html(
    html: str,
    base_url: str,
    external_only: bool = True
) -> list[str]:
    """
    HTML에서 모든 링크를 추출합니다.
    
    Args:
        html: HTML 문자열
        base_url: 상대 URL 해석을 위한 기준 URL
        external_only: True면 외부 링크만 반환
        
    Returns:
        정규화된 URL 목록
    """
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    
    # <a href="..."> 태그 추출
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        
        # 자바스크립트, mailto, tel 등 제외
        if href.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            continue
        
        # 상대 URL을 절대 URL로 변환
        try:
            absolute_url = urljoin(base_url, href)
        except Exception:
            continue
        
        # http/https 프로토콜만 허용
        parsed = urlparse(absolute_url)
        if parsed.scheme not in ("http", "https"):
            continue
        
        # 호스트가 없는 URL 제외
        if not parsed.netloc:
            continue
        
        # 외부 링크만 필터링 (옵션)
        if external_only and not is_external_link(base_url, absolute_url):
            continue
        
        # URL 정규화
        normalized = normalize_url(absolute_url)
        if normalized:
            links.add(normalized)
    
    return list(links)


def filter_by_keywords(
    urls: list[str],
    keywords: list[str]
) -> tuple[list[str], list[str]]:
    """
    URL을 키워드 매칭 여부로 분류합니다.
    
    Args:
        urls: URL 목록
        keywords: 검사할 키워드 목록
        
    Returns:
        (키워드 포함 URL 목록, 키워드 미포함 URL 목록) 튜플
    """
    matched: list[str] = []
    unmatched: list[str] = []
    
    # 키워드를 소문자로 변환
    keywords_lower = [k.lower().strip() for k in keywords if k.strip()]
    
    for url in urls:
        url_lower = url.lower()
        
        # 키워드가 URL에 포함되어 있는지 검사
        if any(kw in url_lower for kw in keywords_lower):
            matched.append(url)
        else:
            unmatched.append(url)
    
    return matched, unmatched


def extract_domains_from_urls(urls: list[str]) -> set[str]:
    """
    URL 목록에서 고유한 Apex 도메인들을 추출합니다.
    
    Args:
        urls: URL 목록
        
    Returns:
        고유 도메인 집합
    """
    domains: set[str] = set()
    
    for url in urls:
        domain = extract_apex_domain(url)
        if domain:
            domains.add(domain)
    
    return domains
