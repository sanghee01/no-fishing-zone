"""
===========================================
📄 main.py - Search-AI 메인 엔트리포인트
===========================================
정적 데이터 로드 + 동적 크롤링을 통합 관리합니다.

실행 방법:
  uv run python main.py
또는:
  docker compose up search-ai
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from crawler.engine import CrawlerEngine
from collectors.static_worker import StaticWorker
from utils.logging_config import setup_logging, get_logger

# 환경 변수 로드
load_dotenv()


async def run_static_import(seeds_dir: Path, backend_url: str) -> dict:
    """
    정적 데이터를 DB에 적재합니다.
    
    Args:
        seeds_dir: seeds 디렉토리 경로
        backend_url: 백엔드 URL
        
    Returns:
        적재 결과
    """
    logger = get_logger()
    logger.info("=" * 50)
    logger.info("📦 정적 데이터 적재 시작")
    logger.info("=" * 50)
    
    worker = StaticWorker(seeds_dir, backend_url)
    results = await worker.run_all()
    
    logger.info(f"✅ 화이트리스트: {results['whitelist_count']}개 도메인")
    logger.info(f"✅ PhishTank: {results['phishtank_success']}개 성공")
    
    return {
        "worker": worker,
        "results": results
    }


async def run_crawler(
    seeds_dir: Path,
    react_ai_url: str,
    backend_url: str,
    whitelist: set[str],
    max_urls: int = 500
) -> dict:
    """
    동적 크롤링을 실행합니다.
    
    Args:
        seeds_dir: seeds 디렉토리 경로
        react_ai_url: react-ai URL
        backend_url: 백엔드 URL
        whitelist: 화이트리스트 도메인
        max_urls: 최대 처리 URL 수
        
    Returns:
        크롤링 결과
    """
    logger = get_logger()
    logger.info("=" * 50)
    logger.info("🕷️ 도메인 홉 크롤링 시작")
    logger.info("=" * 50)
    
    async with CrawlerEngine(
        react_ai_url=react_ai_url,
        backend_url=backend_url
    ) as engine:
        # 시드 로드
        engine.load_seeds(seeds_dir)
        
        # 화이트리스트 설정
        if whitelist:
            engine.set_whitelist(whitelist)
        
        # 크롤링 실행
        stats = await engine.run(max_urls=max_urls)
        
        return stats


async def main():
    """
    메인 함수
    
    1단계: 정적 데이터 적재 (PhishTank)
    2단계: 동적 크롤링 (도메인 홉)
    """
    # 로깅 설정
    logger = setup_logging()
    
    logger.info("🛡️ Search-AI 지능형 도메인 홉 크롤러")
    logger.info("🛡️ Aegis Link Project")
    logger.info("=" * 50)
    
    # 환경 변수에서 설정 로드
    seeds_dir = Path(os.getenv("SEEDS_DIR", PROJECT_ROOT / "seeds"))
    react_ai_url = os.getenv("REACT_AI_URL", "http://ai:8001")
    backend_url = os.getenv("BACKEND_URL", "http://api:8000")
    max_urls = int(os.getenv("MAX_URLS", "500"))
    skip_static = os.getenv("SKIP_STATIC_IMPORT", "").lower() == "true"
    
    logger.info(f"📁 Seeds 디렉토리: {seeds_dir}")
    logger.info(f"🤖 React-AI URL: {react_ai_url}")
    logger.info(f"🦀 Backend URL: {backend_url}")
    logger.info(f"🔢 최대 URL 수: {max_urls}")
    
    whitelist: set[str] = set()
    
    # 1단계: 정적 데이터 적재
    if not skip_static:
        try:
            static_result = await run_static_import(seeds_dir, backend_url)
            whitelist = static_result["worker"].whitelist
        except Exception as e:
            logger.error(f"❌ 정적 데이터 적재 실패: {e}")
            logger.info("⚠️ 크롤링은 계속 진행합니다...")
    else:
        logger.info("⏭️ 정적 데이터 적재 건너뜀 (SKIP_STATIC_IMPORT=true)")
    
    # 2단계: 동적 크롤링
    try:
        crawler_stats = await run_crawler(
            seeds_dir=seeds_dir,
            react_ai_url=react_ai_url,
            backend_url=backend_url,
            whitelist=whitelist,
            max_urls=max_urls
        )
        
        logger.info("=" * 50)
        logger.info("🏁 Search-AI 작업 완료!")
        logger.info(f"📊 최종 통계: {crawler_stats}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
        raise


def run():
    """동기 진입점 (스크립트 실행용)"""
    asyncio.run(main())


if __name__ == "__main__":
    run()
