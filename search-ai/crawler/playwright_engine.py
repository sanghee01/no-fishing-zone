"""
===========================================
📄 playwright_engine.py - Playwright 크롤링 엔진
===========================================
JavaScript로 렌더링된 동적 페이지의 링크까지 모두 추출합니다.
httpx와 달리 실제 브라우저를 사용하므로 Cloudflare도 우회 가능합니다.

★ 클러스터 워커 시스템을 지원합니다.
"""

import asyncio
import re
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import tldextract

from crawler.domain_hopper import DomainHopper
from crawler.domain_fuzzer import DomainFuzzer, extract_domain_number
from api_client.react_ai_client import ReactAIClient
from api_client.backend_client import BackendClient
from utils.url_normalizer import normalize_url, extract_apex_domain
from utils.url_resolver import is_shortener_url, resolve_final_url
from utils.logging_config import get_logger

logger = get_logger()


# =============================================
# 상수 정의
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
    "privacy", "terms", "policy", "help", 
    "about", "guide", "legal", "tos", "cookie"
}

# 페이지 로드 타임아웃 (밀리초)
PAGE_TIMEOUT = 30000

# 브라우저 설정
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox"
]

# ★ Cloaking 감지용 도메인 (봇 차단 시 리다이렉트되는 도메인)
CLOAKING_DOMAINS = {
    "hugedomains.com",
    "godaddy.com",
    "sedo.com",
    "afternic.com",
    "dan.com",
    "namecheap.com",
    "parking.reg.ru",
    "sedoparking.com"
}

# Cloaking 감지용 페이지 제목 키워드
CLOAKING_TITLE_PATTERNS = {
    "domain for sale",
    "is for sale",
    "buy this domain",
    "domain parking",
    "this domain is parked"
}

# ★ Domain-Level BFS: 내부 링크 수집을 허용할 대형 플랫폼
# 이 도메인들은 피싱 호스팅이 가능하므로 URL 단위로 수집
ALLOW_DEPTH_DOMAINS = {
    "google.com",
    "naver.com",
    "kakao.com",
    "notion.so",
    "notion.site",
    "github.io",
    "vercel.app",
    "netlify.app",
    "pages.dev",
    "githubusercontent.com",
    "docs.google.com",
    "forms.gle",
    "bit.ly",
    "t.co"
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


class PlaywrightEngine:
    """
    Playwright 기반 크롤링 엔진
    
    ★ JavaScript 렌더링 지원
    ★ Cloudflare 우회 가능
    ★ 클러스터 워커 시스템
    """
    
    def __init__(
        self,
        worker_id: int,
        shared_hopper: DomainHopper,
        react_ai_url: str = "http://ai:8001",
        backend_url: str = "http://api:8000",
        keywords: list[str] | None = None,
        whitelist: set[str] | None = None,
        enable_fuzzer: bool = True
    ):
        """
        워커 엔진 초기화
        
        Args:
            worker_id: 워커 ID (1, 2, 3...)
            shared_hopper: 공유 URL 큐 (DomainHopper)
            react_ai_url: react-ai 서버 URL
            backend_url: Rust 백엔드 URL
            keywords: 우선순위 키워드 목록
            whitelist: 화이트리스트 도메인
            enable_fuzzer: Domain Fuzzer 활성화
        """
        self.worker_id = worker_id
        self.worker_name = f"Worker-{worker_id}"
        self.hopper = shared_hopper
        self.react_ai_url = react_ai_url
        self.backend_url = backend_url
        self.keywords = keywords or []
        self.whitelist = whitelist or set()
        self.enable_fuzzer = enable_fuzzer
        
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._react_ai: ReactAIClient | None = None
        self._backend: BackendClient | None = None
        self._fuzzer: DomainFuzzer | None = None
        
        self._running = False
        self._stats = {
            "crawled": 0,
            "analyzed": 0,
            "blocked": 0,
            "warnings": 0,
            "safe": 0,
            "errors": 0,
            "links_found": 0
        }
    
    async def start(self, playwright) -> None:
        """엔진 시작 (브라우저 및 클라이언트 초기화)"""
        logger.info(f"[{self.worker_name}] 🚀 브라우저 시작 중...")
        
        # Chromium 브라우저 시작
        self._browser = await playwright.chromium.launch(
            headless=True,
            args=BROWSER_ARGS
        )
        
        # 브라우저 컨텍스트 (세션)
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # API 클라이언트
        self._react_ai = ReactAIClient(base_url=self.react_ai_url)
        self._backend = BackendClient(base_url=self.backend_url)
        await self._react_ai.__aenter__()
        await self._backend.__aenter__()
        
        # Fuzzer
        if self.enable_fuzzer:
            self._fuzzer = DomainFuzzer()
            await self._fuzzer.__aenter__()
        
        logger.info(f"[{self.worker_name}] ✅ 브라우저 준비 완료")
    
    async def stop(self) -> None:
        """엔진 종료"""
        self._running = False
        
        if self._fuzzer:
            await self._fuzzer.__aexit__(None, None, None)
        if self._react_ai:
            await self._react_ai.__aexit__(None, None, None)
        if self._backend:
            await self._backend.__aexit__(None, None, None)
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        
        logger.info(f"[{self.worker_name}] 🛑 브라우저 종료됨")
    
    async def _extract_links(self, page: Page, base_url: str) -> list[str]:
        """
        페이지에서 링크를 추출합니다 (JavaScript 렌더링 후).
        
        ★ Domain-Level BFS 적용:
        - 내부 링크(같은 도메인)는 무시
        - 외부 링크(다른 도메인)만 수집
        - 대형 플랫폼(ALLOW_DEPTH_DOMAINS)은 예외로 내부 링크도 수집
        
        Returns:
            정규화된 외부 링크 URL 목록
        """
        outbound_links: set[str] = set()
        
        # 현재 페이지의 Apex Domain 추출
        current_apex = extract_apex_domain(base_url)
        
        try:
            # 모든 <a> 태그의 href 속성 추출
            elements = await page.locator("a[href]").all()
            
            for element in elements:
                try:
                    href = await element.get_attribute("href")
                    if not href:
                        continue
                    
                    href = href.strip()
                    
                    # 스킵할 패턴
                    if href.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
                        continue
                    
                    # 절대 URL 변환
                    if href.startswith("//"):
                        absolute_url = "https:" + href
                    elif href.startswith("/"):
                        parsed_base = urlparse(base_url)
                        absolute_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                    elif not href.startswith(("http://", "https://")):
                        absolute_url = urljoin(base_url, href)
                    else:
                        absolute_url = href
                    
                    # 정규화
                    normalized = normalize_url(absolute_url)
                    if not normalized:
                        continue
                    
                    # 차단 도메인/정책 페이지 체크
                    if is_blocked_domain(normalized) or is_policy_page(normalized):
                        continue
                    
                    # ★ Domain-Level BFS: 내부 vs 외부 링크 판별
                    link_apex = extract_apex_domain(normalized)
                    
                    # 대형 플랫폼은 예외 (피싱 가능)
                    if link_apex in ALLOW_DEPTH_DOMAINS:
                        outbound_links.add(normalized)
                        continue
                    
                    # 같은 도메인 = 내부 링크 → 무시 (깊게 파지 않음)
                    if link_apex == current_apex:
                        continue
                    
                    # 다른 도메인 = 외부 링크 → 수집 대상!
                    outbound_links.add(normalized)
                
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"[{self.worker_name}] ⚠️ 링크 추출 오류: {e}")
        
        return list(outbound_links)
    
    def _filter_by_keywords(self, urls: list[str]) -> tuple[list[str], list[str]]:
        """키워드 매칭으로 URL 분류"""
        matched: list[str] = []
        unmatched: list[str] = []
        
        keywords_lower = [k.lower().strip() for k in self.keywords if k.strip() and not k.startswith("#")]
        
        for url in urls:
            url_lower = url.lower()
            if any(kw in url_lower for kw in keywords_lower):
                matched.append(url)
            else:
                unmatched.append(url)
        
        return matched, unmatched
    
    async def _analyze_and_save(self, url: str, original_shortener_url: str | None = None) -> dict | None:
        """
        URL을 AI로 분석하고 결과를 DB에 저장
        
        ★ 단축 URL 처리:
        original_shortener_url이 있으면 둘 다 DB에 저장
        bit.ly/abc → example.com/phishing 둘 다 BLOCK 처리됨
        """
        if not self._react_ai or not self._backend:
            return None
        
        domain = extract_apex_domain(url)
        
        # 화이트리스트 체크
        if domain in self.whitelist:
            return None
        
        try:
            # AI 분석 요청 (최종 URL로 분석)
            result = await self._react_ai.analyze_url(url)
            
            if not result:
                return None
            
            self._stats["analyzed"] += 1
            
            status = result.get("status", "SAFE")
            score = result.get("risk_score", 0)
            reasons = result.get("reasons", [])
            
            # 통계 업데이트
            if status == "BLOCK":
                self._stats["blocked"] += 1
                logger.warning(f"[{self.worker_name}] 🚫 BLOCK: {url} (점수: {score})")
            elif status == "WARNING":
                self._stats["warnings"] += 1
                logger.warning(f"[{self.worker_name}] ⚠️ WARNING: {url} (점수: {score})")
            else:
                self._stats["safe"] += 1
            
            description = ", ".join(reasons) if reasons else None
            
            # ★ 최종 URL DB 저장
            await self._backend.upsert_reputation(
                url=url,
                score=score,
                status=status,
                description=description
            )
            
            # ★ 원본 단축 URL도 같은 평판으로 DB 저장
            # bit.ly/abc → BLOCK, example.com/phishing → BLOCK (둘 다!)
            if original_shortener_url:
                await self._backend.upsert_reputation(
                    url=original_shortener_url,
                    score=score,
                    status=status,
                    description=f"→ {url}" if description is None else f"{description} (→ {url})"
                )
                logger.info(
                    f"[{self.worker_name}] 🔗 단축 URL도 저장: "
                    f"{original_shortener_url} → {status}"
                )
            
            return result
        
        except Exception as e:
            logger.debug(f"[{self.worker_name}] ⚠️ 분석 오류: {e}")
            return None
    
    async def _process_url(self, url: str) -> None:
        """
        단일 URL 처리 (크롤링 → Cloaking 감지 → 링크 추출 → AI 분석)
        
        ★ Cloaking Detection: HugeDomains 등으로 리다이렉트 시 WARNING 처리
        ★ Dead Site Skip: 연결 오류 시 즉시 DEAD 처리
        """
        if not self._context:
            return
        
        original_shortener_url = None  # 원본 단축 URL 저장 (나중에 DB 저장용)
        
        # ★ 단축 URL 리졸브: bit.ly, form.gl 등 → 최종 URL
        if is_shortener_url(url):
            logger.info(f"[{self.worker_name}] 🔗 단축 URL 감지: {url}")
            resolved_url = await resolve_final_url(url)
            if resolved_url != url:
                logger.info(f"[{self.worker_name}] ➡️ 최종 URL: {resolved_url}")
                original_shortener_url = url  # 원본 저장
                url = resolved_url  # 최종 URL로 교체
        
        original_domain = extract_apex_domain(url)
        logger.info(f"[{self.worker_name}] 🕷️ {url} 진입...")
        
        page = None
        try:
            page = await self._context.new_page()
            
            # 페이지 로드
            response = await page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            
            if not response:
                logger.debug(f"[{self.worker_name}] ⚠️ 응답 없음")
                # Dead site → 빠른 스킵
                await self._save_dead_site(url)
                return
            
            status = response.status
            
            if status >= 400:
                logger.debug(f"[{self.worker_name}] ⚠️ HTTP {status}")
                self._stats["errors"] += 1
                return
            
            # ★ Cloaking Detection: 리다이렉트된 최종 URL 확인
            final_url = page.url
            final_domain = extract_apex_domain(final_url)
            
            # Cloaking 도메인으로 리다이렉트됨
            if final_domain in CLOAKING_DOMAINS:
                logger.warning(
                    f"[{self.worker_name}] 🎭 Cloaking 감지! "
                    f"{original_domain} → {final_domain}"
                )
                await self._save_cloaking_site(url, original_domain, final_domain)
                return
            
            # ★ 페이지 제목으로 Cloaking 감지
            try:
                title = await page.title()
                title_lower = title.lower() if title else ""
                for pattern in CLOAKING_TITLE_PATTERNS:
                    if pattern in title_lower:
                        logger.warning(
                            f"[{self.worker_name}] 🎭 Cloaking 감지 (제목)! "
                            f"{url} - '{title}'"
                        )
                        await self._save_cloaking_site(url, original_domain, "parking")
                        return
            except:
                pass
            
            self._stats["crawled"] += 1
            
            # JavaScript 렌더링 대기
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass  # 타임아웃이어도 계속 진행
            
            # 링크 추출
            links = await self._extract_links(page, url)
            self._stats["links_found"] += len(links)
            
            if links:
                # 키워드 분류
                high_priority, normal = self._filter_by_keywords(links)
                
                # 큐에 추가
                added = self.hopper.add_urls(normal, high_priority=high_priority)
                
                logger.info(
                    f"[{self.worker_name}] 🔗 링크 {len(links)}개 발견, "
                    f"{added}개 추가 (고우선 {len(high_priority)}개)"
                )
            else:
                logger.debug(f"[{self.worker_name}] ⚠️ 링크 없음")
            
            # AI 분석 (★ 원본 단축 URL도 전달)
            result = await self._analyze_and_save(url, original_shortener_url)
            
            # Fuzzer (위험 사이트인 경우)
            if result and result.get("status") in ("BLOCK", "WARNING") and self._fuzzer:
                extracted = tldextract.extract(url)
                if extract_domain_number(extracted.domain):
                    async for fuzzed_url in self._fuzzer.fuzz_domain(url, offset_range=2):
                        self.hopper.add_url(fuzzed_url, priority=5)
                        logger.warning(f"[{self.worker_name}] 🔢 Fuzz 발견: {fuzzed_url}")
        
        except Exception as e:
            error_msg = str(e).lower()
            # ★ Dead Site Skip: 연결 오류 시 즉시 DEAD 처리
            if any(err in error_msg for err in ["nxdomain", "refused", "timeout", "unreachable"]):
                logger.debug(f"[{self.worker_name}] 💀 Dead site: {url}")
                await self._save_dead_site(url)
            else:
                logger.debug(f"[{self.worker_name}] ❌ 오류: {e}")
            self._stats["errors"] += 1
        
        finally:
            if page:
                await page.close()
    
    async def _save_cloaking_site(self, url: str, original_domain: str, target: str) -> None:
        """Cloaking 사이트를 DB에 WARNING으로 저장"""
        if not self._backend:
            return
        
        try:
            await self._backend.upsert_reputation(
                url=url,
                score=50,
                status="WARNING",
                description=f"Anti-Bot Cloaking Detected: {original_domain} → {target}"
            )
            self._stats["warnings"] += 1
        except:
            pass
    
    async def _save_dead_site(self, url: str) -> None:
        """Dead 사이트를 DB에 저장 (AI 분석 스킵)"""
        if not self._backend:
            return
        
        try:
            # NOTE: 백엔드는 SAFE/WARNING/BLOCK만 지원
            # DEAD 사이트는 SAFE (점수 0)으로 저장
            await self._backend.upsert_reputation(
                url=url,
                score=0,
                status="SAFE",  # DEAD → SAFE (백엔드 호환성)
                description="Dead site - connection failed"
            )
        except:
            pass
    
    async def run(self, max_urls: int = 500) -> dict:
        """
        크롤링 실행
        
        Args:
            max_urls: 최대 처리 URL 수
            
        Returns:
            크롤링 통계
        """
        self._running = True
        processed = 0
        
        logger.info(f"[{self.worker_name}] 🚀 크롤링 시작 (최대 {max_urls}개)")
        
        while self._running and processed < max_urls:
            # 다음 URL 선택 (공유 큐에서)
            url = self.hopper.get_next_url()
            
            if not url:
                # 큐가 비었으면 잠시 대기
                logger.debug(f"[{self.worker_name}] 💤 큐 대기 중...")
                await asyncio.sleep(2)
                continue
            
            # URL 처리
            await self._process_url(url)
            processed += 1
            
            # 진행 상황 (50개마다)
            if processed % 50 == 0:
                logger.info(
                    f"[{self.worker_name}] 📊 진행: {processed}/{max_urls} | "
                    f"링크: {self._stats['links_found']} | "
                    f"분석: {self._stats['analyzed']}"
                )
            
            # 쿨다운 (동일 도메인 연속 방지)
            await asyncio.sleep(0.5)
        
        self._running = False
        
        logger.info(
            f"[{self.worker_name}] 🏁 크롤링 완료! "
            f"처리: {processed}, 링크: {self._stats['links_found']}, "
            f"차단: {self._stats['blocked']}"
        )
        
        return self._stats
