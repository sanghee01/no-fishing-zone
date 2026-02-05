"""
===========================================
📄 engine.py - 비동기 크롤링 엔진 Ver.3
===========================================
Search-AI의 핵심 크롤링 엔진입니다.
도메인 홉 전략과 AI 분석 파이프라인을 통합합니다.

Ver.3 추가 기능:
- SNS 도메인 차단 (instagram, twitter, facebook, x.com)
- 약관/정책 페이지 회피 (privacy, terms, policy)
- Agent ID 로깅 (엔트리 포인트별 추적)
- Domain Morphing Fuzzer 연동
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import httpx

from crawler.domain_hopper import DomainHopper
from crawler.link_extractor import (
    extract_links_from_html,
    filter_by_keywords,
)
from crawler.domain_fuzzer import DomainFuzzer, extract_domain_number
from api_client.react_ai_client import ReactAIClient
from api_client.backend_client import BackendClient
from utils.headers import get_request_headers
from utils.url_normalizer import normalize_url, extract_apex_domain
from utils.logging_config import get_logger

logger = get_logger()


# =============================================
# Ver.3 상수 정의
# =============================================

# SNS 도메인 (크롤링 차단)
BLOCKED_DOMAINS = {
    "instagram.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "threads.net"
}

# 약관/정책 페이지 경로 패턴 (회피 대상)
POLICY_PATH_PATTERNS = {
    "privacy",
    "terms",
    "policy",
    "help",
    "about",
    "guide",
    "legal",
    "tos",
    "cookie",
    "disclaimer"
}


def is_blocked_domain(url: str) -> bool:
    """SNS 등 차단 도메인인지 확인"""
    domain = extract_apex_domain(url)
    return domain in BLOCKED_DOMAINS


def is_policy_page(url: str) -> bool:
    """약관/정책 페이지인지 확인"""
    try:
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        for pattern in POLICY_PATH_PATTERNS:
            if pattern in path_lower:
                return True
        return False
    except Exception:
        return False


def extract_agent_name(url: str) -> str:
    """
    URL에서 Agent 이름을 추출합니다.
    
    예: https://gall.dcinside.com/board/lists/?id=lotto_new2 → Agent-Lotto
    """
    try:
        parsed = urlparse(url)
        
        # DC갤러리: id 파라미터에서 추출
        if "dcinside.com" in parsed.netloc:
            if "loan" in url:
                return "Agent-Loan"
            elif "lotto" in url:
                return "Agent-Lotto"
            elif "stock" in url:
                return "Agent-Stock"
            return "Agent-DCGallery"
        
        # 도메인 기반
        domain = extract_apex_domain(url)
        if "juso" in domain or "link" in domain:
            return "Agent-Portal"
        elif "bobaedream" in domain:
            return "Agent-Bobae"
        elif "linktr" in domain or "lit.link" in domain:
            return "Agent-LinkTree"
        elif "webtoon" in domain or "toki" in domain:
            return "Agent-Webtoon"
        
        return "Agent-Default"
    except Exception:
        return "Agent-Default"


class CrawlerEngine:
    """
    지능형 도메인 홉 크롤러 엔진 Ver.3
    
    주요 기능:
    1. 비동기 HTTP 요청 (httpx)
    2. 도메인 홉 전략 (동일 도메인 연속 방문 방지)
    3. 키워드 기반 우선순위 큐
    4. AI 분석 파이프라인 연동
    5. Self-Feeding (큐가 비면 DB에서 새 Seed 주입)
    6. Backoff 로직 (403/429 응답 시)
    
    Ver.3 추가:
    7. SNS 도메인 차단
    8. 약관/정책 페이지 회피
    9. Agent ID 로깅
    10. Domain Morphing Fuzzer
    
    Attributes:
        hopper: 도메인 홉 전략 관리자
        keywords: 우선순위 키워드 목록
        whitelist: 화이트리스트 도메인
        semaphore: HTTP 요청 동시성 제한
        current_agent: 현재 크롤링 중인 에이전트 ID
    """
    
    def __init__(
        self,
        react_ai_url: str = "http://ai:8001",
        backend_url: str = "http://api:8000",
        max_concurrent_crawl: int = 10,
        max_concurrent_analyze: int = 5,
        request_timeout: float = 30.0,
        enable_fuzzer: bool = True
    ):
        """
        크롤러 엔진 초기화
        
        Args:
            react_ai_url: react-ai 서버 URL
            backend_url: Rust 백엔드 URL
            max_concurrent_crawl: 최대 동시 크롤링 수
            max_concurrent_analyze: 최대 동시 AI 분석 수
            request_timeout: HTTP 요청 타임아웃
            enable_fuzzer: Domain Fuzzer 활성화 여부
        """
        self.react_ai_url = react_ai_url
        self.backend_url = backend_url
        
        self.hopper = DomainHopper()
        self.keywords: list[str] = []
        self.whitelist: set[str] = set()
        
        self.crawl_semaphore = asyncio.Semaphore(max_concurrent_crawl)
        self.analyze_semaphore = asyncio.Semaphore(max_concurrent_analyze)
        self.request_timeout = request_timeout
        
        self._http_client: httpx.AsyncClient | None = None
        self._react_ai_client: ReactAIClient | None = None
        self._backend_client: BackendClient | None = None
        self._fuzzer: DomainFuzzer | None = None
        
        self._enable_fuzzer = enable_fuzzer
        self._running = False
        self._current_agent = "Agent-Default"
        
        self._stats = {
            "crawled": 0,
            "analyzed": 0,
            "blocked": 0,
            "warnings": 0,
            "safe": 0,
            "errors": 0,
            "sns_blocked": 0,
            "policy_skipped": 0,
            "fuzzed_found": 0
        }
    
    async def __aenter__(self) -> "CrawlerEngine":
        """Context manager 진입"""
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.request_timeout),
            http2=True,
            follow_redirects=True,
            max_redirects=5
        )
        self._react_ai_client = ReactAIClient(
            base_url=self.react_ai_url,
            max_concurrent=5  # Claude API 부하 방지
        )
        self._backend_client = BackendClient(
            base_url=self.backend_url
        )
        
        if self._enable_fuzzer:
            self._fuzzer = DomainFuzzer()
            await self._fuzzer.__aenter__()
        
        await self._react_ai_client.__aenter__()
        await self._backend_client.__aenter__()
        
        return self
    
    async def __aexit__(self, *args) -> None:
        """Context manager 종료"""
        if self._http_client:
            await self._http_client.aclose()
        if self._react_ai_client:
            await self._react_ai_client.__aexit__(*args)
        if self._backend_client:
            await self._backend_client.__aexit__(*args)
        if self._fuzzer:
            await self._fuzzer.__aexit__(*args)
    
    def load_seeds(self, seeds_dir: Path) -> int:
        """
        시드 파일들을 로드합니다.
        
        Args:
            seeds_dir: seeds 디렉토리 경로
            
        Returns:
            로드된 엔트리 포인트 개수
        """
        count = 0
        
        # 엔트리 포인트 로드
        entry_file = seeds_dir / "entry_points.txt"
        if entry_file.exists():
            with open(entry_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 주석 및 빈 줄 제외
                    if line and not line.startswith("#"):
                        # 괄호 안의 설명 제거
                        if "(" in line:
                            line = line.split("(")[0].strip()
                        
                        url = normalize_url(line)
                        if url and self.hopper.add_url(url, priority=0):
                            count += 1
            
            logger.info(f"[Crawler] 📍 엔트리 포인트 로드: {count}개")
        
        # 키워드 로드
        keywords_file = seeds_dir / "keywords.txt"
        if keywords_file.exists():
            with open(keywords_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 주석 및 빈 줄 제외
                    if line and not line.startswith("#"):
                        self.keywords.append(line)
            
            logger.info(f"[Crawler] 🔑 키워드 로드: {len(self.keywords)}개")
        
        return count
    
    def set_whitelist(self, domains: set[str]) -> None:
        """
        화이트리스트 도메인을 설정합니다.
        
        Args:
            domains: 신뢰 도메인 집합
        """
        self.whitelist = domains
        logger.info(f"[Crawler] ✅ 화이트리스트 설정: {len(domains)}개 도메인")
    
    def _should_skip_url(self, url: str) -> tuple[bool, str]:
        """
        URL을 스킵해야 하는지 확인합니다.
        
        Args:
            url: 확인할 URL
            
        Returns:
            (스킵 여부, 이유) 튜플
        """
        # SNS 차단
        if is_blocked_domain(url):
            self._stats["sns_blocked"] += 1
            return True, "SNS 도메인"
        
        # 약관 페이지 회피
        if is_policy_page(url):
            self._stats["policy_skipped"] += 1
            return True, "정책 페이지"
        
        # 화이트리스트
        domain = extract_apex_domain(url)
        if domain in self.whitelist:
            return True, "화이트리스트"
        
        return False, ""
    
    async def _fetch_page(self, url: str) -> tuple[str | None, int]:
        """
        페이지를 비동기로 가져옵니다.
        
        Args:
            url: 요청 URL
            
        Returns:
            (HTML 콘텐츠, HTTP 상태 코드) 튜플
        """
        if not self._http_client:
            raise RuntimeError("클라이언트가 초기화되지 않았습니다.")
        
        domain = extract_apex_domain(url)
        
        # 도메인 딜레이 적용
        delay = self.hopper.get_domain_delay(domain)
        if delay > 0:
            logger.debug(f"[{self._current_agent}] ⏳ 딜레이 대기: {delay:.1f}초")
            await asyncio.sleep(delay)
        
        async with self.crawl_semaphore:
            try:
                response = await self._http_client.get(
                    url,
                    headers=get_request_headers()
                )
                
                status = response.status_code
                
                # 403/429 → Backoff
                if status in (403, 429):
                    self.hopper.add_to_backoff(domain)
                    self._stats["errors"] += 1
                    return None, status
                
                # 성공
                if status == 200:
                    content_type = response.headers.get("content-type", "")
                    if "text/html" in content_type:
                        self._stats["crawled"] += 1
                        return response.text, status
                
                return None, status
                
            except httpx.TimeoutException:
                logger.debug(f"[{self._current_agent}] ⏰ 타임아웃: {url}")
                self._stats["errors"] += 1
                return None, 0
            except Exception as e:
                logger.debug(f"[{self._current_agent}] ❌ 요청 오류: {e}")
                self._stats["errors"] += 1
                return None, 0
    
    async def _analyze_and_save(self, url: str) -> dict | None:
        """
        URL을 AI로 분석하고 결과를 DB에 저장합니다.
        
        Args:
            url: 분석할 URL
            
        Returns:
            분석 결과 (없으면 None)
        """
        if not self._react_ai_client or not self._backend_client:
            return None
        
        domain = extract_apex_domain(url)
        
        # 화이트리스트 체크
        if domain in self.whitelist:
            logger.debug(f"[{self._current_agent}] ✅ 화이트리스트: {domain}")
            return None
        
        async with self.analyze_semaphore:
            # AI 분석 요청
            result = await self._react_ai_client.analyze_url(url)
            
            if not result:
                return None
            
            self._stats["analyzed"] += 1
            
            status = result.get("status", "SAFE")
            score = result.get("risk_score", 0)
            reasons = result.get("reasons", [])
            
            # 통계 업데이트
            if status == "BLOCK":
                self._stats["blocked"] += 1
                logger.warning(
                    f"[{self._current_agent}] 🚫 BLOCK: {url} "
                    f"(점수: {score})"
                )
            elif status == "WARNING":
                self._stats["warnings"] += 1
                logger.warning(
                    f"[{self._current_agent}] ⚠️ WARNING: {url} "
                    f"(점수: {score})"
                )
            else:
                self._stats["safe"] += 1
            
            # DB 저장
            await self._backend_client.upsert_reputation(
                url=url,
                score=score,
                status=status,
                description=", ".join(reasons) if reasons else None
            )
            
            return result
    
    async def _run_fuzzer(self, url: str) -> None:
        """
        Domain Fuzzer를 실행하여 숫자 변조 도메인을 탐지합니다.
        
        Args:
            url: 원본 URL
        """
        if not self._fuzzer or not self._enable_fuzzer:
            return
        
        # 도메인에 숫자가 있는지 확인
        domain = extract_apex_domain(url)
        import tldextract
        extracted = tldextract.extract(url)
        
        if not extract_domain_number(extracted.domain):
            return
        
        # Fuzzer 실행
        async for fuzzed_url in self._fuzzer.fuzz_domain(url, offset_range=2):
            self._stats["fuzzed_found"] += 1
            
            # 큐에 추가 (높은 우선순위)
            if self.hopper.add_url(fuzzed_url, priority=5):
                logger.warning(
                    f"[Fuzzer] 🔢 변조 도메인 큐 추가: {fuzzed_url}"
                )
    
    async def _process_url(self, url: str) -> None:
        """
        단일 URL을 처리합니다 (크롤링 → 분석 → 링크 추출 → Fuzzer).
        
        Args:
            url: 처리할 URL
        """
        # Agent ID 업데이트
        self._current_agent = extract_agent_name(url)
        
        # 스킵 여부 확인
        should_skip, reason = self._should_skip_url(url)
        if should_skip:
            logger.debug(f"[{self._current_agent}] ⏭️ 스킵: {url} ({reason})")
            return
        
        logger.info(f"[{self._current_agent}] 🕷️ 크롤링: {url}")
        
        # 페이지 가져오기
        html, status = await self._fetch_page(url)
        
        if not html:
            logger.debug(f"[{self._current_agent}] ⚠️ 로드 실패 [{status}]")
            return
        
        # AI 분석
        result = await self._analyze_and_save(url)
        
        # Domain Fuzzer 실행 (위험 사이트인 경우)
        if result and result.get("status") in ("BLOCK", "WARNING"):
            await self._run_fuzzer(url)
        
        # 링크 추출 (외부 링크만)
        links = extract_links_from_html(html, url, external_only=True)
        
        # SNS/정책 페이지 필터링
        filtered_links = [
            link for link in links 
            if not is_blocked_domain(link) and not is_policy_page(link)
        ]
        
        if filtered_links:
            # 키워드 매칭으로 분류
            high_priority, normal = filter_by_keywords(filtered_links, self.keywords)
            
            # 큐에 추가
            added = self.hopper.add_urls(normal, high_priority=high_priority)
            
            logger.info(
                f"[{self._current_agent}] 🔗 링크: {len(filtered_links)}개 발견, "
                f"{added}개 추가 (고우선 {len(high_priority)}개)"
            )
        
        # BLOCK/WARNING인 경우 해당 사이트 내부 링크도 추가 (재귀적 확장)
        if result and result.get("status") in ("BLOCK", "WARNING"):
            internal_links = extract_links_from_html(html, url, external_only=False)
            internal_count = 0
            for link in internal_links[:20]:  # 내부 링크는 최대 20개
                if not is_policy_page(link) and self.hopper.add_url(link, priority=20):
                    internal_count += 1
            
            if internal_count > 0:
                logger.info(
                    f"[{self._current_agent}] ⚠️ 위험 사이트! "
                    f"내부 링크 {internal_count}개 추가"
                )
    
    async def run(
        self,
        max_urls: int = 1000,
        self_feed_callback: Callable[[], list[str]] | None = None
    ) -> dict:
        """
        크롤링을 시작합니다.
        
        Args:
            max_urls: 최대 처리 URL 수
            self_feed_callback: Self-Feeding 콜백 (큐가 비었을 때 호출)
            
        Returns:
            크롤링 통계
        """
        self._running = True
        processed = 0
        
        logger.info(f"[Crawler] 🚀 크롤링 시작 (최대 {max_urls}개 URL)")
        logger.info(f"[Crawler] 📊 초기 큐 크기: {self.hopper.queue_size}")
        logger.info(f"[Crawler] 🚫 차단 도메인: {BLOCKED_DOMAINS}")
        
        while self._running and processed < max_urls:
            # 다음 URL 선택
            url = self.hopper.get_next_url()
            
            if not url:
                # 큐가 비었음 → Self-Feeding 시도
                if self_feed_callback:
                    logger.info("[Crawler] 🔄 Self-Feeder: 새로운 Seed 주입 시도...")
                    new_seeds = self_feed_callback()
                    
                    if new_seeds:
                        added = self.hopper.add_urls(new_seeds)
                        logger.info(f"[Crawler] 🔄 Self-Feeder: {added}개 URL 주입됨")
                        continue
                
                logger.info("[Crawler] 📭 큐가 비었습니다. 크롤링 종료.")
                break
            
            # URL 처리
            await self._process_url(url)
            processed += 1
            
            # 진행 상황 로깅 (50개마다)
            if processed % 50 == 0:
                stats = self.hopper.get_stats()
                logger.info(
                    f"[Crawler] 📊 진행: {processed}/{max_urls} | "
                    f"큐: {stats['queue_size']} | "
                    f"분석: {self._stats['analyzed']} | "
                    f"차단: {self._stats['blocked']} | "
                    f"Fuzz: {self._stats['fuzzed_found']}"
                )
        
        self._running = False
        
        final_stats = {
            **self._stats,
            "processed": processed,
            "queue_remaining": self.hopper.queue_size,
            "visited_total": self.hopper.visited_count
        }
        
        logger.info("=" * 50)
        logger.info("[Crawler] 🏁 크롤링 완료!")
        logger.info(f"   처리: {processed}개")
        logger.info(f"   크롤링: {self._stats['crawled']}개")
        logger.info(f"   분석: {self._stats['analyzed']}개")
        logger.info(f"   차단: {self._stats['blocked']}개")
        logger.info(f"   경고: {self._stats['warnings']}개")
        logger.info(f"   SNS 차단: {self._stats['sns_blocked']}개")
        logger.info(f"   정책 스킵: {self._stats['policy_skipped']}개")
        logger.info(f"   Fuzz 발견: {self._stats['fuzzed_found']}개")
        logger.info("=" * 50)
        
        return final_stats
    
    def stop(self) -> None:
        """크롤링을 중지합니다."""
        logger.info("[Crawler] 🛑 크롤링 중지 요청...")
        self._running = False
