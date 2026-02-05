"""
===========================================
📄 domain_fuzzer.py - 도메인 숫자 변조 탐지
===========================================
newtoki469 → newtoki470 같은 도메인 숫자 변조(Morphing) 기법을 탐지합니다.
±2 범위 내에서만 후보를 생성하여 무차별 대입을 방지합니다.
"""

import re
import asyncio
from typing import AsyncGenerator

import httpx
import tldextract

from utils.logging_config import get_logger

logger = get_logger()

# 도메인 끝 숫자 패턴 (예: newtoki469 → 469 추출)
TRAILING_NUMBER_PATTERN = re.compile(r"^(.*?)(\d+)$")


def extract_domain_number(domain: str) -> tuple[str, int] | None:
    """
    도메인 이름에서 끝 숫자를 추출합니다.
    
    Args:
        domain: 도메인 이름 (예: newtoki469)
        
    Returns:
        (베이스 이름, 숫자) 튜플 또는 None
        예: ("newtoki", 469)
    """
    match = TRAILING_NUMBER_PATTERN.match(domain)
    if match and match.group(1):  # 베이스가 있어야 함
        return match.group(1), int(match.group(2))
    return None


def generate_fuzz_candidates(url: str, offset_range: int = 2) -> list[str]:
    """
    숫자 변조 후보 URL을 생성합니다.
    
    Args:
        url: 원본 URL
        offset_range: 오프셋 범위 (기본 ±2 = 4개 후보)
        
    Returns:
        후보 URL 목록
    """
    extracted = tldextract.extract(url)
    domain = extracted.domain
    suffix = extracted.suffix
    
    result = extract_domain_number(domain)
    if not result:
        return []
    
    base, number = result
    candidates = []
    
    # ±1, ±2 후보 생성 (0 이하는 제외)
    for offset in range(-offset_range, offset_range + 1):
        if offset == 0:
            continue
        new_number = number + offset
        if new_number <= 0:
            continue
        
        new_domain = f"{base}{new_number}"
        
        # URL 재구성
        if extracted.subdomain:
            new_url = f"https://{extracted.subdomain}.{new_domain}.{suffix}/"
        else:
            new_url = f"https://{new_domain}.{suffix}/"
        
        candidates.append(new_url)
    
    return candidates


class DomainFuzzer:
    """
    도메인 숫자 변조 탐지기
    
    숫자 변조된 도메인 후보를 생성하고 HEAD 요청으로 존재 여부를 확인합니다.
    """
    
    def __init__(
        self,
        timeout: float = 5.0,
        max_concurrent: int = 5
    ):
        """
        초기화
        
        Args:
            timeout: HEAD 요청 타임아웃 (초)
            max_concurrent: 최대 동시 요청 수
        """
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None
        self._checked_domains: set[str] = set()
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            verify=False  # SSL 검증 비활성화 (불법 사이트 대응)
        )
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    async def check_url_alive(self, url: str) -> bool:
        """
        URL이 살아있는지 HEAD 요청으로 확인합니다.
        
        Args:
            url: 확인할 URL
            
        Returns:
            200~399 응답이면 True
        """
        async with self.semaphore:
            try:
                response = await self._client.head(url)
                return 200 <= response.status_code < 400
            except Exception:
                return False
    
    async def fuzz_domain(
        self,
        url: str,
        offset_range: int = 2
    ) -> AsyncGenerator[str, None]:
        """
        도메인 숫자 변조 후보를 검사하고 살아있는 도메인을 반환합니다.
        
        Args:
            url: 원본 URL
            offset_range: 오프셋 범위 (기본 ±2)
            
        Yields:
            살아있는 변조 도메인 URL
        """
        candidates = generate_fuzz_candidates(url, offset_range)
        
        if not candidates:
            return
        
        extracted = tldextract.extract(url)
        original_domain = f"{extracted.domain}.{extracted.suffix}"
        
        # 중복 체크 방지
        if original_domain in self._checked_domains:
            return
        self._checked_domains.add(original_domain)
        
        logger.info(
            f"[Fuzzer] 🔢 숫자 변조 탐지 시작: {extracted.domain} "
            f"(후보 {len(candidates)}개)"
        )
        
        # 병렬 확인
        tasks = [self.check_url_alive(candidate) for candidate in candidates]
        results = await asyncio.gather(*tasks)
        
        for candidate, is_alive in zip(candidates, results):
            if is_alive:
                logger.warning(f"[Fuzzer] 🚨 변조 도메인 발견: {candidate}")
                yield candidate
    
    def clear_cache(self):
        """체크 캐시 초기화"""
        self._checked_domains.clear()
