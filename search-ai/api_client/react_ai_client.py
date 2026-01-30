"""
===========================================
📄 react_ai_client.py - React-AI 서버 통신
===========================================
react-ai 서버(Claude AI 분석 엔진)와 통신하는 클라이언트입니다.
"""

import asyncio
import uuid
from typing import Literal

import httpx

from utils.logging_config import get_logger

logger = get_logger()

# react-ai 서버 기본 URL (Docker 내부 네트워크)
REACT_AI_URL = "http://ai:8001"


class ReactAIClient:
    """
    react-ai 서버와 비동기 통신을 수행하는 클라이언트
    
    Attributes:
        base_url: react-ai 서버 URL
        semaphore: 동시 요청 제한 세마포어
        client: httpx 비동기 클라이언트
    """
    
    def __init__(
        self, 
        base_url: str = REACT_AI_URL,
        max_concurrent: int = 10,
        timeout: float = 60.0
    ):
        """
        클라이언트를 초기화합니다.
        
        Args:
            base_url: react-ai 서버 URL
            max_concurrent: 최대 동시 요청 수 (Claude API 부하 방지)
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> "ReactAIClient":
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
    
    async def analyze_url(self, url: str) -> dict | None:
        """
        URL을 react-ai 서버에 분석 요청합니다.
        
        Semaphore로 동시 요청을 제한하여 Claude API 부하를 방지합니다.
        
        Args:
            url: 분석할 URL
            
        Returns:
            분석 결과 딕셔너리:
            - url: 분석된 URL
            - status: "SAFE" | "WARNING" | "BLOCK"
            - risk_score: 0-100 정수
            - category: 콘텐츠 카테고리
            - reasons: 위험 사유 목록
        """
        if not self._client:
            raise RuntimeError("클라이언트가 초기화되지 않았습니다. async with 문을 사용하세요.")
        
        request_id = str(uuid.uuid4())
        
        async with self.semaphore:
            try:
                logger.debug(f"🔍 AI 분석 요청: {url}")
                
                response = await self._client.post(
                    f"{self.base_url}/analyze",
                    json={
                        "url": url,
                        "request_id": request_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(
                        f"✅ AI 분석 완료: {url} → "
                        f"{result.get('status')} (점수: {result.get('risk_score')})"
                    )
                    return result
                else:
                    logger.warning(
                        f"⚠️ AI 분석 실패 [{response.status_code}]: {url}"
                    )
                    return None
                    
            except httpx.TimeoutException:
                logger.error(f"⏰ AI 분석 타임아웃: {url}")
                return None
            except Exception as e:
                logger.error(f"❌ AI 분석 오류: {url} - {e}")
                return None
    
    async def batch_analyze(
        self, 
        urls: list[str],
        delay_between: float = 0.5
    ) -> list[dict]:
        """
        여러 URL을 배치로 분석합니다.
        
        Args:
            urls: 분석할 URL 목록
            delay_between: 요청 간 딜레이 (초)
            
        Returns:
            성공한 분석 결과 목록
        """
        results = []
        
        for i, url in enumerate(urls):
            result = await self.analyze_url(url)
            if result:
                results.append(result)
            
            # 마지막 요청이 아니면 딜레이
            if i < len(urls) - 1:
                await asyncio.sleep(delay_between)
        
        return results
