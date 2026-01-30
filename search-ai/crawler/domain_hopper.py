"""
===========================================
📄 domain_hopper.py - 도메인 홉 전략
===========================================
동일 도메인 연속 방문을 방지하고 도메인 간 이동을 최적화합니다.
"""

import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from heapq import heappush, heappop
from typing import Iterator

from utils.url_normalizer import extract_apex_domain
from utils.logging_config import get_logger

logger = get_logger()


@dataclass(order=True)
class PrioritizedURL:
    """
    우선순위가 부여된 URL
    
    priority가 낮을수록 높은 우선순위 (min-heap)
    """
    priority: int
    url: str = field(compare=False)
    domain: str = field(compare=False)
    added_at: float = field(compare=False, default_factory=time.time)


class DomainHopper:
    """
    도메인 홉 전략을 관리하는 클래스
    
    핵심 전략:
    1. 동일 도메인 연속 방문 방지
    2. 키워드 매칭 URL 우선 처리
    3. Backoff 대상 도메인 회피
    4. 최근 방문 도메인 추적
    
    Attributes:
        queue: 우선순위 큐 (URL 저장)
        visited_urls: 방문한 URL 집합
        recently_visited_domains: 최근 방문 도메인 (순환 버퍼)
        backoff_domains: 일시 차단된 도메인
        domain_last_visit: 도메인별 마지막 방문 시각
    """
    
    def __init__(
        self,
        max_recent_domains: int = 10,
        backoff_duration: float = 1800.0,  # 30분
        min_domain_delay: float = 3.0,
        max_domain_delay: float = 10.0
    ):
        """
        초기화
        
        Args:
            max_recent_domains: 최근 방문 도메인 추적 개수
            backoff_duration: Backoff 지속 시간 (초)
            min_domain_delay: 도메인 재방문 최소 딜레이 (초)
            max_domain_delay: 도메인 재방문 최대 딜레이 (초)
        """
        self.queue: list[PrioritizedURL] = []
        self.visited_urls: set[str] = set()
        self.recently_visited_domains: list[str] = []
        self.max_recent_domains = max_recent_domains
        
        self.backoff_domains: dict[str, float] = {}  # domain -> backoff_until
        self.backoff_duration = backoff_duration
        
        self.domain_last_visit: dict[str, float] = {}
        self.min_domain_delay = min_domain_delay
        self.max_domain_delay = max_domain_delay
        
        self._url_in_queue: set[str] = set()  # 큐 내 URL 중복 체크용
    
    def add_url(self, url: str, priority: int = 50) -> bool:
        """
        URL을 큐에 추가합니다.
        
        Args:
            url: 추가할 URL
            priority: 우선순위 (0=최고, 100=최저)
            
        Returns:
            추가 성공 여부 (중복/이미 방문 시 False)
        """
        # 이미 방문했거나 큐에 있으면 건너뜀
        if url in self.visited_urls or url in self._url_in_queue:
            return False
        
        domain = extract_apex_domain(url)
        if not domain:
            return False
        
        # Backoff 중인 도메인이면 건너뜀
        if self._is_backed_off(domain):
            logger.debug(f"⏳ Backoff 중인 도메인: {domain}")
            return False
        
        item = PrioritizedURL(
            priority=priority,
            url=url,
            domain=domain
        )
        
        heappush(self.queue, item)
        self._url_in_queue.add(url)
        
        return True
    
    def add_urls(
        self,
        urls: list[str],
        high_priority: list[str] | None = None
    ) -> int:
        """
        여러 URL을 한 번에 추가합니다.
        
        Args:
            urls: 일반 우선순위 URL 목록
            high_priority: 높은 우선순위 URL 목록 (키워드 매칭)
            
        Returns:
            실제 추가된 URL 개수
        """
        count = 0
        
        # 높은 우선순위 URL (priority=10)
        if high_priority:
            for url in high_priority:
                if self.add_url(url, priority=10):
                    count += 1
        
        # 일반 우선순위 URL (priority=50)
        for url in urls:
            if self.add_url(url, priority=50):
                count += 1
        
        return count
    
    def get_next_url(self) -> str | None:
        """
        다음에 방문할 URL을 선택합니다.
        
        도메인 홉 전략:
        1. 최근 방문 도메인이 아닌 URL 우선
        2. 여러 후보 중 랜덤 선택 (예측 불가성)
        3. 도메인 딜레이 적용
        
        Returns:
            다음 URL (큐가 비었으면 None)
        """
        if not self.queue:
            return None
        
        # 후보군 수집 (상위 20개 검토)
        candidates: list[PrioritizedURL] = []
        temp_storage: list[PrioritizedURL] = []
        
        check_count = min(20, len(self.queue))
        
        for _ in range(check_count):
            if not self.queue:
                break
            
            item = heappop(self.queue)
            
            # Backoff 체크
            if self._is_backed_off(item.domain):
                continue
            
            # 최근 방문 도메인이 아니면 후보로
            if item.domain not in self.recently_visited_domains:
                candidates.append(item)
            else:
                temp_storage.append(item)
        
        # 후보가 없으면 temp_storage에서 선택
        if not candidates:
            candidates = temp_storage
            temp_storage = []
        
        if not candidates:
            # 큐에 남은 것들 복원
            for item in temp_storage:
                heappush(self.queue, item)
            return None
        
        # 후보 중 랜덤 선택 (우선순위 상위 5개 중)
        top_candidates = sorted(candidates, key=lambda x: x.priority)[:5]
        selected = random.choice(top_candidates)
        
        # 선택되지 않은 후보들 복원
        for item in candidates:
            if item.url != selected.url:
                heappush(self.queue, item)
        for item in temp_storage:
            heappush(self.queue, item)
        
        # 방문 처리
        self._mark_visited(selected.url, selected.domain)
        self._url_in_queue.discard(selected.url)
        
        return selected.url
    
    def _mark_visited(self, url: str, domain: str) -> None:
        """방문 기록 업데이트"""
        self.visited_urls.add(url)
        
        # 최근 방문 도메인 업데이트 (순환 버퍼)
        if domain in self.recently_visited_domains:
            self.recently_visited_domains.remove(domain)
        self.recently_visited_domains.append(domain)
        
        if len(self.recently_visited_domains) > self.max_recent_domains:
            self.recently_visited_domains.pop(0)
        
        self.domain_last_visit[domain] = time.time()
    
    def add_to_backoff(self, domain: str) -> None:
        """
        도메인을 Backoff 목록에 추가합니다.
        (403/429 응답 시 호출)
        
        Args:
            domain: Backoff 대상 도메인
        """
        until = time.time() + self.backoff_duration
        self.backoff_domains[domain] = until
        logger.warning(f"🚫 Backoff 시작: {domain} ({self.backoff_duration/60:.0f}분)")
    
    def _is_backed_off(self, domain: str) -> bool:
        """도메인이 Backoff 중인지 확인"""
        if domain not in self.backoff_domains:
            return False
        
        if time.time() >= self.backoff_domains[domain]:
            # Backoff 만료
            del self.backoff_domains[domain]
            logger.info(f"✅ Backoff 해제: {domain}")
            return False
        
        return True
    
    def get_domain_delay(self, domain: str) -> float:
        """
        도메인 재방문 딜레이를 계산합니다.
        
        Args:
            domain: 대상 도메인
            
        Returns:
            권장 딜레이 (초)
        """
        if domain not in self.domain_last_visit:
            return 0.0
        
        elapsed = time.time() - self.domain_last_visit[domain]
        min_wait = random.uniform(self.min_domain_delay, self.max_domain_delay)
        
        if elapsed < min_wait:
            return min_wait - elapsed
        
        return 0.0
    
    @property
    def queue_size(self) -> int:
        """큐에 남은 URL 개수"""
        return len(self.queue)
    
    @property
    def visited_count(self) -> int:
        """방문한 URL 개수"""
        return len(self.visited_urls)
    
    def is_empty(self) -> bool:
        """큐가 비었는지 확인"""
        return len(self.queue) == 0
    
    def get_stats(self) -> dict:
        """통계 정보 반환"""
        return {
            "queue_size": self.queue_size,
            "visited_count": self.visited_count,
            "backoff_domains": len(self.backoff_domains),
            "recent_domains": self.recently_visited_domains.copy()
        }
