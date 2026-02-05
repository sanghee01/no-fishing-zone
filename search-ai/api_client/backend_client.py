"""
===========================================
📄 backend_client.py - Rust 백엔드 서버 통신
===========================================
Rust 백엔드(Axum + SeaORM)와 통신하는 클라이언트입니다.
URL 평판 정보를 DB에 저장하고 조회합니다.
"""

import asyncio
from typing import Literal

import httpx

from utils.logging_config import get_logger

logger = get_logger()

# Rust 백엔드 서버 기본 URL (Docker 내부 네트워크)
BACKEND_URL = "http://api:8000"

# URL 상태 타입
UrlStatus = Literal["SAFE", "WARNING", "BLOCK"]


class BackendClient:
    """
    Rust 백엔드 서버와 비동기 통신을 수행하는 클라이언트
    
    Attributes:
        base_url: 백엔드 서버 URL
        semaphore: 동시 요청 제한 세마포어
        client: httpx 비동기 클라이언트
    """
    
    def __init__(
        self,
        base_url: str = BACKEND_URL,
        max_concurrent: int = 20,
        timeout: float = 30.0
    ):
        """
        클라이언트를 초기화합니다.
        
        Args:
            base_url: 백엔드 서버 URL
            max_concurrent: 최대 동시 요청 수
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> "BackendClient":
        """Context manager 진입"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            http2=True
        )
        return self
    
    async def __aexit__(self, *args) -> None:
        """Context manager 종료"""
        if self._client:
            await self._client.aclose()
    
    async def upsert_reputation(
        self,
        url: str,
        score: int,
        status: UrlStatus,
        description: str | None = None
    ) -> bool:
        """
        URL 평판 정보를 DB에 저장합니다 (Upsert).
        
        Rust 서버에서 ON CONFLICT 처리가 되어 있어
        중복 URL은 업데이트됩니다.
        
        Args:
            url: 대상 URL
            score: 위험 점수 (0-100)
            status: 상태 ("SAFE" | "WARNING" | "BLOCK")
            description: 설명 (선택)
            
        Returns:
            성공 여부
        """
        if not self._client:
            raise RuntimeError("클라이언트가 초기화되지 않았습니다.")
        
        # ★ 422 에러 방지: 데이터 형변환
        safe_score = int(score) if score is not None else 0
        safe_score = max(0, min(100, safe_score))  # 0-100 범위 보장
        
        safe_status = str(status).upper() if status else "SAFE"
        if safe_status not in ("SAFE", "WARNING", "BLOCK"):
            safe_status = "SAFE"  # 잘못된 상태는 SAFE로 폴백
        
        # description 길이 제한 (500자)
        safe_description = None
        if description:
            safe_description = str(description)[:500]
        
        payload = {
            "url": url,
            "score": safe_score,
            "status": safe_status,
            "description": safe_description
        }
        
        async with self.semaphore:
            try:
                response = await self._client.post(
                    f"{self.base_url}/url-reputations/",
                    json=payload
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ DB 저장 완료: {url}")
                    return True
                else:
                    # ★ 422 에러 시 payload 로깅
                    logger.warning(
                        f"⚠️ DB 저장 실패 [{response.status_code}]: {url} | "
                        f"Payload: score={safe_score}, status={safe_status}"
                    )
                    return False
                    
            except Exception as e:
                logger.error(f"❌ DB 저장 오류: {url} - {e}")
                return False
    
    async def batch_upsert(
        self,
        items: list[dict],
        batch_size: int = 1000,
        delay_between_batches: float = 0.1
    ) -> tuple[int, int]:
        """
        여러 URL 평판 정보를 배치로 저장합니다.
        
        PostgreSQL 부하 방지를 위해 1,000개씩 끊어서 전송하고
        배치 간 0.1초 딜레이를 줍니다.
        
        Args:
            items: 저장할 항목 목록 (dict: url, score, status, description)
            batch_size: 배치 크기 (기본 1000)
            delay_between_batches: 배치 간 딜레이 (초)
            
        Returns:
            (성공 개수, 실패 개수) 튜플
        """
        success_count = 0
        fail_count = 0
        total = len(items)
        
        logger.info(f"📦 배치 저장 시작: 총 {total}개, 배치 크기 {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info(f"📤 배치 {batch_num}/{total_batches} 전송 중... ({len(batch)}개)")
            
            # 배치 내 항목들을 동시에 전송
            tasks = [
                self.upsert_reputation(
                    url=item["url"],
                    score=item["score"],
                    status=item["status"],
                    description=item.get("description")
                )
                for item in batch
            ]
            
            results = await asyncio.gather(*tasks)
            
            batch_success = sum(1 for r in results if r)
            batch_fail = len(results) - batch_success
            
            success_count += batch_success
            fail_count += batch_fail
            
            logger.info(
                f"✅ 배치 {batch_num} 완료: "
                f"성공 {batch_success}/{len(batch)} "
                f"(누적: {success_count}/{total})"
            )
            
            # 다음 배치 전 딜레이 (마지막 배치 제외)
            if i + batch_size < total:
                await asyncio.sleep(delay_between_batches)
        
        logger.info(f"📦 배치 저장 완료: 성공 {success_count}, 실패 {fail_count}")
        
        return success_count, fail_count
    
    async def get_unanalyzed_urls(self, limit: int = 50) -> list[str]:
        """
        DB에서 아직 충분히 분석되지 않은 URL들을 가져옵니다.
        (Self-Feeding을 위한 메서드)
        
        NOTE: 현재 Rust 백엔드에 이 엔드포인트가 없으므로,
              향후 구현이 필요합니다. 지금은 빈 리스트 반환.
        
        Args:
            limit: 가져올 최대 개수
            
        Returns:
            URL 목록
        """
        # TODO: Rust 백엔드에 GET /url-reputations/unanalyzed 엔드포인트 필요
        logger.debug(f"🔄 Self-Feeder: DB에서 미분석 URL 조회 (limit={limit})")
        return []
