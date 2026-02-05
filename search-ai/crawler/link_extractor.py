"""
===========================================
📄 link_extractor.py - 링크 추출기 Ver.3.1
===========================================
HTML 페이지에서 링크를 추출하고 필터링합니다.

Ver.3.1 수정:
- 디버그 로깅 추가
- 상대 경로 변환 강화
- 추출 통계 로깅
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
    
    # 디버깅용 카운터
    total_anchors = 0
    skipped_js = 0
    skipped_internal = 0
    skipped_invalid = 0
    
    # <a href="..."> 태그 추출
    for anchor in soup.find_all("a", href=True):
        total_anchors += 1
        href = anchor["href"]
        
        # 빈 href 제외
        if not href or not href.strip():
            skipped_invalid += 1
            continue
        
        href = href.strip()
        
        # 자바스크립트, mailto, tel 등 제외
        if href.startswith(("javascript:", "mailto:", "tel:", "#", "data:", "void(")):
            skipped_js += 1
            continue
        
        # 상대 URL을 절대 URL로 변환
        try:
            # /로 시작하는 상대 경로 처리
            if href.startswith("//"):
                absolute_url = "https:" + href
            elif href.startswith("/"):
                parsed_base = urlparse(base_url)
                absolute_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
            elif not href.startswith(("http://", "https://")):
                absolute_url = urljoin(base_url, href)
            else:
                absolute_url = href
        except Exception:
            skipped_invalid += 1
            continue
        
        # http/https 프로토콜만 허용
        parsed = urlparse(absolute_url)
        if parsed.scheme not in ("http", "https"):
            skipped_invalid += 1
            continue
        
        # 호스트가 없는 URL 제외
        if not parsed.netloc:
            skipped_invalid += 1
            continue
        
        # 외부 링크만 필터링 (옵션)
        if external_only and not is_external_link(base_url, absolute_url):
            skipped_internal += 1
            continue
        
        # URL 정규화
        normalized = normalize_url(absolute_url)
        if normalized:
            links.add(normalized)
        else:
            skipped_invalid += 1
    
    # 디버그 로깅 (링크가 0개일 때 특히 유용)
    if len(links) == 0 and total_anchors > 0:
        logger.debug(
            f"[LinkExtractor] ⚠️ 0개 추출 | "
            f"총 앵커: {total_anchors}, JS: {skipped_js}, "
            f"내부: {skipped_internal}, 무효: {skipped_invalid}"
        )
    
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
    
    # 키워드를 소문자로 변환 + 주석 제외
    keywords_lower = [
        k.lower().strip() 
        for k in keywords 
        if k.strip() and not k.strip().startswith("#")
    ]
    
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
