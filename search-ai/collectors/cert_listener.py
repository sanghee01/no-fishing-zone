"""
===========================================
📄 cert_listener.py - SSL 인증서 실시간 감청
===========================================
CertStream을 통해 전 세계 SSL 인증서 발급 내역을 실시간 모니터링합니다.
피싱 사이트가 개설되기도 전에 탐지할 수 있습니다 (Zero-day 탐지).
"""

import asyncio
import threading
from pathlib import Path
from typing import Callable, Awaitable

import certstream

from utils.logging_config import get_logger

logger = get_logger()


def load_keywords_for_certstream(keywords_path: Path) -> set[str]:
    """
    CertStream 필터링용 키워드를 로드합니다.
    
    Args:
        keywords_path: keywords.txt 경로
        
    Returns:
        소문자 키워드 집합
    """
    keywords: set[str] = set()
    
    if not keywords_path.exists():
        logger.warning(f"[CertStream] ⚠️ 키워드 파일 없음: {keywords_path}")
        return keywords
    
    with open(keywords_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 소문자로 변환하여 저장
            keywords.add(line.lower())
    
    logger.info(f"[CertStream] 📋 키워드 {len(keywords)}개 로드 완료")
    return keywords


class CertStreamListener:
    """
    SSL 인증서 실시간 감청기
    
    전 세계 인증서 발급 스트림에서 키워드 매칭 도메인을 탐지합니다.
    """
    
    def __init__(
        self,
        keywords: set[str],
        on_detect: Callable[[str], Awaitable[None]] | None = None
    ):
        """
        초기화
        
        Args:
            keywords: 필터링 키워드 집합 (소문자)
            on_detect: 탐지 시 호출할 콜백 (async)
        """
        self.keywords = keywords
        self.on_detect = on_detect
        self._running = False
        self._detected_count = 0
        self._total_processed = 0
        self._loop: asyncio.AbstractEventLoop | None = None
    
    def _matches_keywords(self, domain: str) -> str | None:
        """
        도메인이 키워드와 매칭되는지 확인
        
        Args:
            domain: 검사할 도메인 (소문자)
            
        Returns:
            매칭된 키워드 또는 None
        """
        for keyword in self.keywords:
            if keyword in domain:
                return keyword
        return None
    
    def _certstream_callback(self, message, context):
        """
        CertStream 콜백 (동기)
        
        인증서 발급 이벤트를 처리합니다.
        """
        if not self._running:
            return
        
        self._total_processed += 1
        
        if message["message_type"] != "certificate_update":
            return
        
        try:
            # 인증서에 포함된 모든 도메인 추출
            data = message.get("data", {})
            leaf_cert = data.get("leaf_cert", {})
            all_domains = leaf_cert.get("all_domains", [])
            
            for domain in all_domains:
                domain_lower = domain.lower()
                
                # 와일드카드 제거
                if domain_lower.startswith("*."):
                    domain_lower = domain_lower[2:]
                
                # 키워드 매칭
                matched_keyword = self._matches_keywords(domain_lower)
                if matched_keyword:
                    self._detected_count += 1
                    url = f"https://{domain}/"
                    
                    logger.warning(
                        f"[CertStream] 🚨 실시간 감지: {domain} "
                        f"(키워드: {matched_keyword})"
                    )
                    
                    # 비동기 콜백 호출
                    if self.on_detect and self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self.on_detect(url),
                            self._loop
                        )
        
        except Exception as e:
            logger.debug(f"[CertStream] 메시지 파싱 오류: {e}")
    
    async def start(self):
        """
        CertStream 감청을 시작합니다.
        
        별도 스레드에서 certstream을 실행하고 메인 루프와 통신합니다.
        """
        if self._running:
            logger.warning("[CertStream] ⚠️ 이미 실행 중입니다")
            return
        
        logger.info("[CertStream] 🎧 실시간 SSL 인증서 감청 시작...")
        logger.info(f"[CertStream] 📋 필터링 키워드: {len(self.keywords)}개")
        
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        # CertStream은 blocking이므로 별도 스레드에서 실행
        def run_certstream():
            try:
                certstream.listen_for_events(
                    self._certstream_callback,
                    url="wss://certstream.calidog.io/"
                )
            except Exception as e:
                logger.error(f"[CertStream] ❌ 연결 오류: {e}")
                self._running = False
        
        thread = threading.Thread(target=run_certstream, daemon=True)
        thread.start()
        
        # 연결 확인을 위해 잠시 대기
        await asyncio.sleep(2)
        
        if self._running:
            logger.info("[CertStream] ✅ 감청 스트림 연결 완료")
    
    async def run_forever(self):
        """
        CertStream을 시작하고 무한 대기합니다.
        
        주기적으로 통계를 출력합니다.
        """
        await self.start()
        
        stats_interval = 60  # 60초마다 통계
        
        while self._running:
            await asyncio.sleep(stats_interval)
            logger.info(
                f"[CertStream] 📊 통계: "
                f"처리 {self._total_processed}개, "
                f"탐지 {self._detected_count}개"
            )
    
    def stop(self):
        """감청을 중지합니다."""
        self._running = False
        logger.info("[CertStream] 🛑 감청 중지됨")
    
    def get_stats(self) -> dict:
        """통계 정보 반환"""
        return {
            "running": self._running,
            "total_processed": self._total_processed,
            "detected_count": self._detected_count
        }
