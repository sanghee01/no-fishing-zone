"""
===========================================
📄 static_worker.py - 정적 데이터 수집기 Ver.4
===========================================
OpenPhish, Tranco 등 정적 데이터를 파싱하여 DB에 적재합니다.

Ver.4 변경사항:
- PhishTank (Dead URL 다수) → OpenPhish (실시간, 12h 갱신)
- Docker 시작 시 자동 OpenPhish 다운로드
- URL 길이 검증 (2048자 초과 시 스킵)
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import httpx

from api_client.backend_client import BackendClient
from utils.url_normalizer import normalize_url
from utils.logging_config import get_logger

logger = get_logger()

# URL 최대 길이 (PostgreSQL VARCHAR 및 브라우저 한계 고려)
MAX_URL_LENGTH = 2048

# OpenPhish 공개 피드 URL (12시간마다 갱신됨)
OPENPHISH_FEED_URL = "https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt"


async def fetch_openphish_feed() -> list[str]:
    """
    OpenPhish GitHub 피드에서 URL 목록을 다운로드합니다.
    
    Returns:
        피싱 URL 목록
    """
    logger.info(f"[Static] 🌐 OpenPhish 피드 다운로드 중...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(OPENPHISH_FEED_URL)
            response.raise_for_status()
            
            urls = [
                line.strip() 
                for line in response.text.splitlines() 
                if line.strip() and line.strip().startswith("http")
            ]
            
            logger.info(f"[Static] ✅ OpenPhish: {len(urls)}개 URL 다운로드 완료")
            return urls
            
        except Exception as e:
            logger.error(f"[Static] ❌ OpenPhish 다운로드 실패: {e}")
            return []


async def save_openphish_to_file(urls: list[str], output_path: Path) -> bool:
    """
    OpenPhish URL 목록을 파일에 저장합니다 (덮어쓰기).
    
    Args:
        urls: 저장할 URL 목록
        output_path: 저장 경로
        
    Returns:
        성공 여부
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        
        logger.info(f"[Static] 💾 OpenPhish 저장 완료: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"[Static] ❌ OpenPhish 저장 실패: {e}")
        return False


async def load_openphish_data(
    file_path: Path,
    batch_size: int = 500
) -> AsyncGenerator[list[dict], None]:
    """
    OpenPhish TXT 파일을 배치 단위로 로드합니다.
    
    Args:
        file_path: OpenPhish TXT 파일 경로
        batch_size: 배치 크기
        
    Yields:
        URL 평판 정보 딕셔너리 목록
    """
    if not file_path.exists():
        logger.warning(f"[Static] ⚠️ OpenPhish 파일 없음: {file_path}")
        return
    
    logger.info(f"[Static] 📂 OpenPhish 데이터 로드 중: {file_path}")
    
    skipped_count = 0
    processed_count = 0
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total_items = len(lines)
        logger.info(f"[Static] 📊 OpenPhish 항목 수: {total_items}")
        
        batch: list[dict] = []
        
        for line in lines:
            url = line.strip()
            
            if not url or not url.startswith("http"):
                skipped_count += 1
                continue
            
            # URL 정규화
            normalized = normalize_url(url)
            if not normalized:
                skipped_count += 1
                continue
            
            # URL 길이 검증 (2048자 초과 시 스킵)
            if len(normalized) > MAX_URL_LENGTH:
                skipped_count += 1
                logger.debug(f"[Static] ⏭️ URL 너무 김 ({len(normalized)}자)")
                continue
            
            processed_count += 1
            batch.append({
                "url": normalized,
                "score": 100,  # 피싱 사이트는 최고 위험도
                "status": "BLOCK",
                "description": "OpenPhish 블랙리스트"
            })
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # 마지막 배치
        if batch:
            yield batch
        
        logger.info(f"[Static] 📊 처리: {processed_count}개, 스킵: {skipped_count}개")
            
    except Exception as e:
        logger.error(f"[Static] ❌ OpenPhish 로드 오류: {e}")


async def load_whitelist_csv(
    file_path: Path
) -> set[str]:
    """
    화이트리스트 CSV 파일을 로드합니다.
    
    Tranco 형식: 순위,도메인
    
    Args:
        file_path: CSV 파일 경로
        
    Returns:
        도메인 집합
    """
    domains: set[str] = set()
    
    if not file_path.exists():
        logger.warning(f"[Static] ⚠️ 화이트리스트 파일 없음: {file_path}")
        return domains
    
    logger.info(f"[Static] 📂 화이트리스트 로드 중: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Tranco 형식: "1,google.com"
                if "," in line:
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        domain = parts[1].strip().lower()
                        if domain:
                            domains.add(domain)
                else:
                    # 단순 도메인 목록
                    domain = line.lower()
                    if domain:
                        domains.add(domain)
        
        logger.info(f"[Static] ✅ 화이트리스트 로드 완료: {len(domains)}개 도메인")
        
    except Exception as e:
        logger.error(f"[Static] ❌ 화이트리스트 로드 오류: {e}")
    
    return domains


async def import_openphish_to_db(
    openphish_path: Path,
    backend_url: str = "http://api:8000",
    batch_size: int = 500,
    delay_between_batches: float = 0.1
) -> tuple[int, int]:
    """
    OpenPhish 데이터를 Rust 백엔드 DB에 적재합니다.
    
    Args:
        openphish_path: OpenPhish TXT 파일 경로
        backend_url: 백엔드 서버 URL
        batch_size: 배치 크기
        delay_between_batches: 배치 간 딜레이 (초)
        
    Returns:
        (성공 개수, 실패 개수) 튜플
    """
    total_success = 0
    total_fail = 0
    batch_num = 0
    
    async with BackendClient(base_url=backend_url) as client:
        async for batch in load_openphish_data(openphish_path, batch_size):
            batch_num += 1
            
            success, fail = await client.batch_upsert(
                items=batch,
                batch_size=batch_size,
                delay_between_batches=0.05
            )
            
            total_success += success
            total_fail += fail
            
            logger.info(
                f"[Static] 📤 배치 #{batch_num}: {success}개 성공, {fail}개 실패 "
                f"(누적: {total_success}/{total_success + total_fail})"
            )
            
            await asyncio.sleep(delay_between_batches)
    
    logger.info(
        f"[Static] 📦 OpenPhish 적재 완료: "
        f"성공 {total_success}, 실패 {total_fail}"
    )
    
    return total_success, total_fail


class StaticWorker:
    """
    정적 데이터 수집 워커
    
    OpenPhish, Tranco 등 정적 데이터 소스를 관리하고 DB에 적재합니다.
    
    ★ Ver.4: PhishTank → OpenPhish로 변경
    """
    
    def __init__(
        self,
        seeds_dir: Path,
        backend_url: str = "http://api:8000"
    ):
        """
        초기화
        
        Args:
            seeds_dir: seeds 디렉토리 경로
            backend_url: Rust 백엔드 URL
        """
        self.seeds_dir = seeds_dir
        self.backend_url = backend_url
        self.whitelist: set[str] = set()
    
    async def update_openphish(self) -> bool:
        """
        OpenPhish 피드를 다운로드하고 저장합니다.
        
        ★ Docker 시작 시 자동 호출됨
        
        Returns:
            성공 여부
        """
        urls = await fetch_openphish_feed()
        
        if not urls:
            logger.warning("[Static] ⚠️ OpenPhish 피드가 비어있습니다.")
            return False
        
        output_path = self.seeds_dir / "openphish.txt"
        return await save_openphish_to_file(urls, output_path)
    
    async def load_whitelist(self) -> set[str]:
        """
        화이트리스트를 로드합니다.
        
        Returns:
            화이트리스트 도메인 집합
        """
        for filename in ["1000000white.csv", "whitelist.csv", "tranco.csv"]:
            path = self.seeds_dir / filename
            if path.exists():
                self.whitelist = await load_whitelist_csv(path)
                return self.whitelist
        
        logger.info("[Static] 📋 화이트리스트 파일을 찾을 수 없습니다.")
        return set()
    
    async def import_openphish(self) -> tuple[int, int]:
        """
        OpenPhish 데이터를 DB에 적재합니다.
        
        Returns:
            (성공 개수, 실패 개수) 튜플
        """
        path = self.seeds_dir / "openphish.txt"
        
        if path.exists():
            return await import_openphish_to_db(
                openphish_path=path,
                backend_url=self.backend_url
            )
        
        logger.warning("[Static] 📋 OpenPhish 파일을 찾을 수 없습니다. 다운로드 시도...")
        
        # 파일이 없으면 다운로드 후 적재
        if await self.update_openphish():
            return await import_openphish_to_db(
                openphish_path=path,
                backend_url=self.backend_url
            )
        
        return 0, 0
    
    async def run_all(self) -> dict:
        """
        모든 정적 데이터 작업을 실행합니다.
        
        ★ Docker 시작 시 호출됨:
        1. OpenPhish 최신 피드 다운로드
        2. 화이트리스트 로드
        3. OpenPhish 블랙리스트 DB 적재
        
        Returns:
            작업 결과 통계
        """
        results = {
            "whitelist_count": 0,
            "openphish_success": 0,
            "openphish_fail": 0,
            "openphish_updated": False
        }
        
        # ★ Step 1: OpenPhish 최신 피드 다운로드 (항상 실행)
        results["openphish_updated"] = await self.update_openphish()
        
        # Step 2: 화이트리스트 로드
        whitelist = await self.load_whitelist()
        results["whitelist_count"] = len(whitelist)
        
        # Step 3: OpenPhish 블랙리스트 DB 적재
        success, fail = await self.import_openphish()
        results["openphish_success"] = success
        results["openphish_fail"] = fail
        
        return results
