"""
===========================================
📄 main.py - Search-AI Final Evolution
===========================================
★ Playwright 클러스터 크롤러 ★

3개의 워커가 병렬로 크롤링합니다:
- [Worker-1] 🕷️ joosotok.com 진입...
- [Worker-2] 🕷️ jusoping2.net 진입...
- [Worker-3] 🕷️ dcinside.com 진입...

실행 방법:
  docker compose up -d --build search-ai
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from crawler.domain_hopper import DomainHopper
from crawler.playwright_engine import PlaywrightEngine
from collectors.static_worker import StaticWorker
from collectors.cert_listener import CertStreamListener, load_keywords_for_certstream
from utils.logging_config import setup_logging, get_logger
from utils.url_normalizer import normalize_url

# 환경 변수 로드
load_dotenv()

# 워커 휴식 시간 (사이클 사이)
WORKER_REST_INTERVAL = 30


def load_seeds(seeds_dir: Path, hopper: DomainHopper) -> tuple[int, list[str]]:
    """
    시드 파일을 로드하고 공유 큐에 추가합니다.
    
    Returns:
        (엔트리 개수, 키워드 목록) 튜플
    """
    logger = get_logger()
    count = 0
    keywords = []
    
    # 엔트리 포인트 로드
    entry_file = seeds_dir / "entry_points.txt"
    if entry_file.exists():
        with open(entry_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "(" in line:
                        line = line.split("(")[0].strip()
                    url = normalize_url(line)
                    if url and hopper.add_url(url, priority=0):
                        count += 1
        logger.info(f"[Main] 📍 엔트리 포인트: {count}개")
    
    # 키워드 로드
    keywords_file = seeds_dir / "keywords.txt"
    if keywords_file.exists():
        with open(keywords_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keywords.append(line)
        logger.info(f"[Main] 🔑 키워드: {len(keywords)}개")
    
    return count, keywords


async def run_static_import(seeds_dir: Path, backend_url: str) -> set[str]:
    """정적 데이터 적재 후 화이트리스트 반환"""
    logger = get_logger()
    logger.info("[Static] 📦 정적 데이터 적재 시작...")
    
    try:
        worker = StaticWorker(seeds_dir, backend_url)
        results = await worker.run_all()
        logger.info(
            f"[Static] ✅ 화이트리스트: {results['whitelist_count']}개, "
            f"PhishTank: {results['phishtank_success']}개"
        )
        return worker.whitelist
    except Exception as e:
        logger.error(f"[Static] ❌ 오류: {e}")
        return set()


async def run_worker(
    worker_id: int,
    shared_hopper: DomainHopper,
    playwright,
    react_ai_url: str,
    backend_url: str,
    keywords: list[str],
    whitelist: set[str],
    max_urls_per_cycle: int
) -> None:
    """
    단일 워커 무한 루프
    
    Args:
        worker_id: 워커 ID (1, 2, 3)
        shared_hopper: 공유 URL 큐
        playwright: Playwright 인스턴스
        ...
    """
    logger = get_logger()
    cycle = 0
    
    engine = PlaywrightEngine(
        worker_id=worker_id,
        shared_hopper=shared_hopper,
        react_ai_url=react_ai_url,
        backend_url=backend_url,
        keywords=keywords,
        whitelist=whitelist,
        enable_fuzzer=True
    )
    
    while True:
        cycle += 1
        logger.info(f"[Worker-{worker_id}] 🔄 사이클 #{cycle} 시작")
        
        try:
            await engine.start(playwright)
            stats = await engine.run(max_urls=max_urls_per_cycle)
            await engine.stop()
            
            logger.info(
                f"[Worker-{worker_id}] 📊 사이클 #{cycle} 완료: "
                f"처리 {stats.get('crawled', 0)}개, "
                f"차단 {stats.get('blocked', 0)}개"
            )
        
        except Exception as e:
            logger.error(f"[Worker-{worker_id}] ❌ 오류: {e}")
            try:
                await engine.stop()
            except:
                pass
        
        # 휴식
        logger.info(f"[Worker-{worker_id}] 💤 {WORKER_REST_INTERVAL}초 휴식...")
        await asyncio.sleep(WORKER_REST_INTERVAL)


async def run_certstream_daemon(
    seeds_dir: Path,
    react_ai_url: str,
    backend_url: str
) -> None:
    """CertStream 실시간 감청 (무한 루프)"""
    logger = get_logger()
    logger.info("[CertStream] 🎧 실시간 SSL 감청 시작...")
    
    keywords = load_keywords_for_certstream(seeds_dir / "keywords.txt")
    
    if not keywords:
        logger.warning("[CertStream] ⚠️ 키워드 없음, 대기 중...")
        while True:
            await asyncio.sleep(3600)
    
    from api_client.react_ai_client import ReactAIClient
    from api_client.backend_client import BackendClient
    
    while True:
        try:
            react_ai = ReactAIClient(base_url=react_ai_url)
            backend = BackendClient(base_url=backend_url)
            await react_ai.__aenter__()
            await backend.__aenter__()
            
            async def on_detect(url: str):
                try:
                    result = await react_ai.analyze_url(url)
                    if result:
                        await backend.upsert_reputation(
                            url=url,
                            score=result.get("risk_score", 0),
                            status=result.get("status", "SAFE"),
                            description=f"[CertStream] {result.get('reasons', [])}"
                        )
                        if result.get("status") in ("BLOCK", "WARNING"):
                            logger.warning(f"[CertStream] 🚨 {result.get('status')}: {url}")
                except:
                    pass
            
            listener = CertStreamListener(keywords=keywords, on_detect=on_detect)
            await listener.run_forever()
        
        except Exception as e:
            logger.error(f"[CertStream] ❌ 오류: {e}, 10초 후 재시작...")
            await asyncio.sleep(10)


async def main():
    """
    메인 함수 - Playwright 클러스터 시스템
    
    ★ 3개 워커 + CertStream 병렬 실행 ★
    ★ 컨테이너 절대 종료 안 함 ★
    """
    logger = setup_logging()
    
    logger.info("🛡️" + "=" * 48)
    logger.info("🛡️ Search-AI Final Evolution - Playwright Cluster")
    logger.info("🛡️ 3 Workers + CertStream 병렬 실행")
    logger.info("🛡️ Aegis Link Project")
    logger.info("🛡️" + "=" * 48)
    
    # 환경 변수
    seeds_dir = Path(os.getenv("SEEDS_DIR", PROJECT_ROOT / "seeds"))
    react_ai_url = os.getenv("REACT_AI_URL", "http://ai:8001")
    backend_url = os.getenv("BACKEND_URL", "http://api:8000")
    max_urls = int(os.getenv("MAX_URLS", "200"))
    num_workers = int(os.getenv("NUM_WORKERS", "3"))
    skip_static = os.getenv("SKIP_STATIC_IMPORT", "").lower() == "true"
    enable_certstream = os.getenv("ENABLE_CERTSTREAM", "true").lower() == "true"
    
    logger.info(f"[Config] 🕷️ Workers: {num_workers}")
    logger.info(f"[Config] 🔢 Max URLs/Cycle: {max_urls}")
    logger.info(f"[Config] 🎧 CertStream: {'ON' if enable_certstream else 'OFF'}")
    
    # 1. 정적 데이터 적재
    whitelist: set[str] = set()
    if not skip_static:
        whitelist = await run_static_import(seeds_dir, backend_url)
    
    # 2. 공유 큐 생성 및 시드 로드
    shared_hopper = DomainHopper()
    entry_count, keywords = load_seeds(seeds_dir, shared_hopper)
    logger.info(f"[Main] 📊 공유 큐 초기화: {shared_hopper.queue_size}개 URL")
    
    # 3. Playwright 시작
    async with async_playwright() as playwright:
        
        # 워커 태스크 생성
        worker_tasks = [
            run_worker(
                worker_id=i + 1,
                shared_hopper=shared_hopper,
                playwright=playwright,
                react_ai_url=react_ai_url,
                backend_url=backend_url,
                keywords=keywords,
                whitelist=whitelist,
                max_urls_per_cycle=max_urls
            )
            for i in range(num_workers)
        ]
        
        # CertStream 태스크
        all_tasks = worker_tasks.copy()
        if enable_certstream:
            all_tasks.append(
                run_certstream_daemon(seeds_dir, react_ai_url, backend_url)
            )
        
        logger.info(f"[Main] 🚀 클러스터 시작: {len(worker_tasks)} Workers + CertStream")
        
        # 모든 태스크 병렬 실행 (무한)
        await asyncio.gather(*all_tasks, return_exceptions=True)
    
    # 여기까지 오면 안 됨
    logger.error("[Main] ⚠️ 모든 태스크 종료됨!")


def run():
    """동기 진입점"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
