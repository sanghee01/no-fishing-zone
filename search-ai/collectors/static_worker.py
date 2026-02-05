"""
===========================================
📄 static_worker.py - 정적 데이터 수집기 Ver.3.1
===========================================
PhishTank, Tranco 등 정적 데이터를 파싱하여 DB에 적재합니다.

Ver.3.1 수정:
- URL 길이 검증 (2048자 초과 시 스킵)
- 배치 카운터 수정
- 상세 로깅 추가
"""

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator

from api_client.backend_client import BackendClient
from utils.url_normalizer import normalize_url
from utils.logging_config import get_logger

logger = get_logger()

# URL 최대 길이 (PostgreSQL VARCHAR 및 브라우저 한계 고려)
MAX_URL_LENGTH = 2048


async def load_phishtank_data(
    file_path: Path,
    batch_size: int = 1000
) -> AsyncGenerator[list[dict], None]:
    """
    PhishTank JSON 파일을 배치 단위로 로드합니다.
    
    메모리 효율을 위해 제너레이터 방식으로 구현했습니다.
    
    Args:
        file_path: PhishTank JSON 파일 경로
        batch_size: 배치 크기
        
    Yields:
        URL 평판 정보 딕셔너리 목록
    """
    if not file_path.exists():
        logger.warning(f"[Static] ⚠️ PhishTank 파일 없음: {file_path}")
        return
    
    logger.info(f"[Static] 📂 PhishTank 데이터 로드 중: {file_path}")
    
    skipped_count = 0
    processed_count = 0
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # PhishTank 형식: 리스트 또는 딕셔너리
        if isinstance(data, dict):
            # {"data": [...]} 형식일 수 있음
            items = data.get("data", data.get("phishes", []))
        elif isinstance(data, list):
            items = data
        else:
            logger.error("[Static] ❌ PhishTank 데이터 형식 오류")
            return
        
        total_items = len(items)
        logger.info(f"[Static] 📊 PhishTank 항목 수: {total_items}")
        
        batch: list[dict] = []
        
        for item in items:
            # PhishTank 형식에 맞게 URL 추출
            url = None
            if isinstance(item, dict):
                url = item.get("url") or item.get("phish_url") or item.get("target")
            elif isinstance(item, str):
                url = item
            
            if not url:
                skipped_count += 1
                continue
            
            # URL 정규화
            normalized = normalize_url(url)
            if not normalized:
                skipped_count += 1
                continue
            
            # ★ URL 길이 검증 (2048자 초과 시 스킵)
            if len(normalized) > MAX_URL_LENGTH:
                skipped_count += 1
                logger.debug(f"[Static] ⏭️ URL 너무 김 ({len(normalized)}자): {normalized[:50]}...")
                continue
            
            processed_count += 1
            batch.append({
                "url": normalized,
                "score": 100,  # 피싱 사이트는 최고 위험도
                "status": "BLOCK",
                "description": "PhishTank 블랙리스트"
            })
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # 마지막 배치
        if batch:
            yield batch
        
        logger.info(f"[Static] 📊 처리: {processed_count}개, 스킵: {skipped_count}개")
            
    except json.JSONDecodeError as e:
        logger.error(f"[Static] ❌ PhishTank JSON 파싱 오류: {e}")
    except Exception as e:
        logger.error(f"[Static] ❌ PhishTank 로드 오류: {e}")


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


async def import_phishtank_to_db(
    phishtank_path: Path,
    backend_url: str = "http://api:8000",
    batch_size: int = 1000,
    delay_between_batches: float = 0.1
) -> tuple[int, int]:
    """
    PhishTank 데이터를 Rust 백엔드 DB에 적재합니다.
    
    Args:
        phishtank_path: PhishTank JSON 파일 경로
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
        async for batch in load_phishtank_data(phishtank_path, batch_size):
            batch_num += 1
            
            success, fail = await client.batch_upsert(
                items=batch,
                batch_size=batch_size,
                delay_between_batches=0.05  # 배치 내부 딜레이
            )
            
            # ★ 누적 카운터 올바르게 갱신
            total_success += success
            total_fail += fail
            
            logger.info(
                f"[Static] 📤 배치 #{batch_num}: {success}개 성공, {fail}개 실패 "
                f"(누적: {total_success}/{total_success + total_fail})"
            )
            
            # 배치 간 딜레이
            await asyncio.sleep(delay_between_batches)
    
    logger.info(
        f"[Static] 📦 PhishTank 적재 완료: "
        f"성공 {total_success}, 실패 {total_fail}"
    )
    
    return total_success, total_fail


class StaticWorker:
    """
    정적 데이터 수집 워커
    
    PhishTank, Tranco 등 정적 데이터 소스를 관리하고 DB에 적재합니다.
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
    
    async def load_whitelist(self) -> set[str]:
        """
        화이트리스트를 로드합니다.
        
        Returns:
            화이트리스트 도메인 집합
        """
        # 1000000white.csv 또는 다른 이름 시도
        for filename in ["1000000white.csv", "whitelist.csv", "tranco.csv"]:
            path = self.seeds_dir / filename
            if path.exists():
                self.whitelist = await load_whitelist_csv(path)
                return self.whitelist
        
        logger.info("[Static] 📋 화이트리스트 파일을 찾을 수 없습니다.")
        return set()
    
    async def import_phishtank(self) -> tuple[int, int]:
        """
        PhishTank 데이터를 DB에 적재합니다.
        
        Returns:
            (성공 개수, 실패 개수) 튜플
        """
        # pished_tank.json 또는 phishtank.json 시도
        for filename in ["pished_tank.json", "phishtank.json"]:
            path = self.seeds_dir / filename
            if path.exists():
                return await import_phishtank_to_db(
                    phishtank_path=path,
                    backend_url=self.backend_url
                )
        
        logger.warning("[Static] 📋 PhishTank 파일을 찾을 수 없습니다.")
        return 0, 0
    
    async def run_all(self) -> dict:
        """
        모든 정적 데이터 작업을 실행합니다.
        
        Returns:
            작업 결과 통계
        """
        results = {
            "whitelist_count": 0,
            "phishtank_success": 0,
            "phishtank_fail": 0
        }
        
        # 화이트리스트 로드
        whitelist = await self.load_whitelist()
        results["whitelist_count"] = len(whitelist)
        
        # PhishTank 적재
        success, fail = await self.import_phishtank()
        results["phishtank_success"] = success
        results["phishtank_fail"] = fail
        
        return results
