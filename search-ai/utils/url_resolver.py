"""
===========================================
📄 url_resolver.py - 최종 URL 추적 유틸리티
===========================================
bit.ly, form.gl 같은 단축 URL을 리다이렉트 후 최종 URL로 변환합니다.

팀원 피드백 반영:
"수집하신 url이 실제 접속된 url과 다를 때 차단 불가능"
→ 단축 URL을 최종 destination URL로 변환하여 DB에 저장

특징:
- HTTP 리다이렉트 체인 추적
- JavaScript 리다이렉트도 지원 (Playwright 사용 시)
- 최대 10회 리다이렉트 제한
"""

import asyncio
from urllib.parse import urlparse

import httpx

from utils.logging_config import get_logger

logger = get_logger()


# 단축 URL 서비스 도메인 목록
URL_SHORTENER_DOMAINS = {
    # 일반 단축 URL
    "bit.ly", "bitly.com",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "ow.ly",
    "is.gd", "v.gd",
    "buff.ly",
    "adf.ly",
    "j.mp",
    "tr.im",
    "cli.gs",
    "short.to",
    "hoo.gl",
    "tiny.cc",
    "lnkd.in",
    "db.tt",
    "qr.ae",
    "rebrand.ly",
    "bl.ink",
    "shorte.st",
    
    # 폼/설문 링크
    "forms.gle",
    "form.gl",
    
    # 링크트리 계열
    "linktr.ee",
    "lit.link",
    "beacons.ai",
    "solo.to",
    "carrd.co",
    
    # 기타
    "t.me",  # 텔레그램
    "wa.me",  # 왓츠앱
    "lin.ee",  # 라인
    "url.kr",  # 한국
    "me2.do",  # 네이버
    "han.gl",  # 한컴
}


def is_shortener_url(url: str) -> bool:
    """
    URL이 단축 URL 서비스인지 확인합니다.
    
    Args:
        url: 확인할 URL
        
    Returns:
        단축 URL이면 True
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # www. 제거
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain in URL_SHORTENER_DOMAINS
    except Exception:
        return False


async def resolve_final_url(url: str, max_redirects: int = 10, timeout: float = 10.0) -> str:
    """
    리다이렉트를 추적하여 최종 URL을 반환합니다.
    
    bit.ly → example.com/phishing-page (최종)
    
    Args:
        url: 추적할 URL
        max_redirects: 최대 리다이렉트 횟수
        timeout: 타임아웃 (초)
        
    Returns:
        최종 URL (리다이렉트 실패 시 원본 URL)
    """
    current_url = url
    
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False  # 수동으로 추적
    ) as client:
        for i in range(max_redirects):
            try:
                response = await client.head(current_url, follow_redirects=False)
                
                # 리다이렉트 상태 코드 (301, 302, 303, 307, 308)
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    
                    if location:
                        # 상대 URL 처리
                        if location.startswith("/"):
                            parsed = urlparse(current_url)
                            location = f"{parsed.scheme}://{parsed.netloc}{location}"
                        
                        logger.debug(f"[Resolver] 🔄 리다이렉트 {i+1}: {current_url} → {location}")
                        current_url = location
                        continue
                
                # 리다이렉트 아님 → 최종 URL
                break
                
            except httpx.TimeoutException:
                logger.debug(f"[Resolver] ⏰ 타임아웃: {current_url}")
                break
            except Exception as e:
                logger.debug(f"[Resolver] ❌ 오류: {e}")
                break
    
    if current_url != url:
        logger.info(f"[Resolver] ✅ 최종 URL: {url} → {current_url}")
    
    return current_url


async def resolve_batch(urls: list[str], concurrency: int = 5) -> dict[str, str]:
    """
    여러 URL을 배치로 리졸브합니다.
    
    Args:
        urls: URL 목록
        concurrency: 동시 요청 수
        
    Returns:
        {원본 URL: 최종 URL} 딕셔너리
    """
    semaphore = asyncio.Semaphore(concurrency)
    results = {}
    
    async def resolve_one(url: str):
        async with semaphore:
            # 단축 URL만 리졸브
            if is_shortener_url(url):
                final = await resolve_final_url(url)
                results[url] = final
            else:
                results[url] = url
    
    tasks = [resolve_one(url) for url in urls]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    return results


# 테스트용
if __name__ == "__main__":
    async def test():
        test_urls = [
            "https://bit.ly/3abc123",
            "https://t.co/xyz789",
            "https://google.com",
        ]
        
        for url in test_urls:
            print(f"Testing: {url}")
            print(f"  Is shortener: {is_shortener_url(url)}")
            if is_shortener_url(url):
                final = await resolve_final_url(url)
                print(f"  Final URL: {final}")
            print()
    
    asyncio.run(test())
