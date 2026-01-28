"""
===========================================
📄 search_verifier.py - Phase 4: 검색 엔진 교차 검증
===========================================
이 파일은 분석 파이프라인의 마지막 단계(Phase 4)를 담당합니다.

교차 검증이란?
- AI가 찾은 브랜드명으로 검색엔진에서 검색
- 검색 결과의 공식 도메인과 현재 URL을 비교
- 다르면 "사칭 사이트" 의심

예시:
- AI가 "신한은행"이라는 keyword 추출
- 구글에서 "신한은행" 검색 → 결과 1위: shinhan.com
- 현재 URL이 shinhann.com이면? → 타이포스쿼팅!

점수 체계:
- 유사/변조 (Typosquatting): +50점 (결정타)
- 검색 결과에 없음: +30점
- 완전 일치: 0점 (정상)
"""

import httpx  # 비동기 HTTP 클라이언트
import logging  # 로그 기록용
from urllib.parse import quote  # URL 인코딩용
from typing import List, Tuple  # 타입 힌트용

from Levenshtein import distance as levenshtein_distance  # 문자열 유사도
from bs4 import BeautifulSoup  # HTML 파싱

from app.config import (
    TYPOSQUATTING_SCORE,       # 타이포스쿼팅 점수 (+50)
    MISMATCH_SCORE,            # 불일치 점수 (+30)
    LEVENSHTEIN_THRESHOLD_MIN,  # 편집거리 최소 (1)
    LEVENSHTEIN_THRESHOLD_MAX,  # 편집거리 최대 (3)
    REQUEST_TIMEOUT,           # 요청 타임아웃
    USER_AGENT                 # 브라우저 위장
)
from app.models import PhaseResult  # Phase 결과 모델
from app.utils.domain import extract_apex_domain  # 도메인 추출

logger = logging.getLogger(__name__)

# ============================================
# 검색 엔진 URL 템플릿
# ============================================
# {keyword} 부분에 검색어가 들어감
NAVER_SEARCH_URL = "https://search.naver.com/search.naver?query={keyword}"
GOOGLE_SEARCH_URL = "https://www.google.com/search?q={keyword}"


async def fetch_search_results(keyword: str) -> List[str]:
    """
    Google과 Naver에서 키워드를 검색하고 상위 도메인을 추출합니다.
    
    Args:
        keyword: 검색할 키워드 (예: "신한은행")
        
    Returns:
        List[str]: 검색 결과 상위 도메인 목록 (최대 5개)
        
    동작 원리:
    1. 키워드를 URL 인코딩 (한글 → %XX 형태)
    2. 네이버/구글 검색 페이지 요청
    3. HTML에서 링크 추출
    4. 각 링크에서 apex 도메인 추출
    5. 중복 제거 후 상위 5개 반환
    """
    domains = []  # 결과 도메인 목록
    
    # 한글 키워드를 URL에서 사용할 수 있게 인코딩
    # 예: "신한은행" → "%EC%8B%A0%ED%95%9C%EC%9D%80%ED%96%89"
    encoded_keyword = quote(keyword)
    
    # HTTP 요청 헤더 (검색엔진이 봇으로 차단하지 않도록 브라우저로 위장)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=headers) as client:
        # ============================================
        # 네이버 검색
        # ============================================
        try:
            naver_url = NAVER_SEARCH_URL.format(keyword=encoded_keyword)
            response = await client.get(naver_url)
            
            if response.status_code == 200:
                # HTML 파싱
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 모든 링크 태그에서 href 추출
                for link in soup.select("a[href]"):
                    href = link.get("href", "")
                    
                    # http로 시작하고 네이버가 아닌 외부 링크만
                    if href.startswith("http") and "naver.com" not in href:
                        apex = extract_apex_domain(href)
                        
                        # 중복 체크 후 추가
                        if apex and apex not in domains:
                            domains.append(apex)
                            
                            # 5개 모으면 종료
                            if len(domains) >= 5:
                                break
                                
        except Exception as e:
            logger.warning(f"⚠️ 네이버 검색 실패: {e}")
        
        # ============================================
        # 구글 검색
        # ============================================
        try:
            google_url = GOOGLE_SEARCH_URL.format(keyword=encoded_keyword)
            response = await client.get(google_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                for link in soup.select("a[href]"):
                    href = link.get("href", "")
                    
                    # 구글은 링크를 /url?q=실제URL&... 형태로 래핑함
                    # 이것을 풀어서 실제 URL 추출
                    if "/url?q=" in href:
                        start = href.find("/url?q=") + 7  # "/url?q=" 다음부터
                        end = href.find("&", start)  # 다음 & 전까지
                        if end == -1:
                            end = len(href)
                        href = href[start:end]
                    
                    if href.startswith("http") and "google.com" not in href:
                        apex = extract_apex_domain(href)
                        
                        if apex and apex not in domains:
                            domains.append(apex)
                            
                            # 구글에서는 더 많이 수집 (검색 결과가 더 정확함)
                            if len(domains) >= 10:
                                break
                                
        except Exception as e:
            logger.warning(f"⚠️ 구글 검색 실패: {e}")
    
    # 최종적으로 상위 5개만 반환
    return domains[:5]


def check_similarity(target_domain: str, search_domains: List[str]) -> Tuple[str, int]:
    """
    현재 도메인과 검색 결과 도메인들의 유사도를 비교합니다.
    
    Args:
        target_domain: 분석 중인 URL의 도메인
        search_domains: 검색 결과에서 추출한 도메인 목록
        
    Returns:
        Tuple[match_type, score]:
        - match_type: "match"(일치), "similar"(유사=타이포스쿼팅), "mismatch"(불일치)
        - score: 부여할 점수
        
    Levenshtein Distance(편집 거리)란?
    - 두 문자열을 같게 만드는 데 필요한 최소 편집 횟수
    - 예: shinhan → shinhann = 거리 1 (n 하나 추가)
    - 거리가 1~3이면 "비슷하지만 다름" = 타이포스쿼팅 의심
    """
    # 분석 대상 도메인의 apex 추출
    target_apex = extract_apex_domain(target_domain).lower()
    
    # 검색 결과가 없으면 판단 불가
    if not search_domains:
        return ("unknown", 0)
    
    # ============================================
    # 1. 먼저 완전 일치 검사
    # ============================================
    for domain in search_domains:
        if domain.lower() == target_apex:
            # 검색 결과와 완전히 일치 = 정상 사이트
            return ("match", 0)
    
    # ============================================
    # 2. 타이포스쿼팅 검사 (유사도 비교)
    # ============================================
    min_distance = float("inf")  # 최소 편집 거리
    closest_domain = ""  # 가장 유사한 도메인
    
    for domain in search_domains:
        # Levenshtein 거리 계산
        dist = levenshtein_distance(target_apex, domain.lower())
        
        if dist < min_distance:
            min_distance = dist
            closest_domain = domain
    
    # 편집 거리가 1~3이면 타이포스쿼팅
    # (0은 완전 일치, 4 이상은 너무 달라서 우연의 일치)
    if LEVENSHTEIN_THRESHOLD_MIN <= min_distance <= LEVENSHTEIN_THRESHOLD_MAX:
        return ("similar", TYPOSQUATTING_SCORE)  # +50점 (결정타!)
    
    # ============================================
    # 3. 검색 결과에 없음 = 불일치
    # ============================================
    # 브랜드라고 주장하지만 검색해도 안 나옴
    return ("mismatch", MISMATCH_SCORE)  # +30점


async def verify_with_search(url: str, keyword: str) -> PhaseResult:
    """
    검색 엔진을 통해 URL의 진위를 검증합니다.
    
    Args:
        url: 분석 중인 URL
        keyword: Phase 3에서 AI가 추출한 브랜드명
        
    Returns:
        PhaseResult: Phase 4 분석 결과
        
    동작 원리:
    1. keyword가 없으면 건너뜀
    2. 검색 엔진에서 keyword 검색
    3. 검색 결과 도메인과 현재 URL 도메인 비교
    4. 유사도에 따라 점수 부여
    """
    # 키워드가 없으면 검증 불가
    if not keyword:
        return PhaseResult(
            phase="Phase 4: Search Verification",
            score=0,
            reasons=["키워드 없음 - 단계 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"skipped": True, "reason": "No keyword"}
        )
    
    try:
        # ============================================
        # 검색 엔진에서 결과 가져오기
        # ============================================
        search_domains = await fetch_search_results(keyword)
        
        if not search_domains:
            return PhaseResult(
                phase="Phase 4: Search Verification",
                score=0,
                reasons=["검색 결과 없음 - 단계 건너뜀"],
                should_block=False,
                skip_remaining=False,
                metadata={"skipped": True, "reason": "No search results"}
            )
        
        # 분석 대상 URL의 도메인 추출
        target_domain = extract_apex_domain(url)
        
        # ============================================
        # 유사도 비교
        # ============================================
        match_type, score = check_similarity(target_domain, search_domains)
        
        reasons = []
        metadata = {
            "keyword": keyword,
            "target_domain": target_domain,
            "search_results": search_domains,
            "match_type": match_type
        }
        
        # 결과 메시지 생성
        if match_type == "match":
            # ✅ 정상: 검색 결과와 일치
            reasons.append(f"도메인 검증 완료: {target_domain}이(가) 검색 결과와 일치")
            
        elif match_type == "similar":
            # 🚨 타이포스쿼팅: 유사하지만 다름
            reasons.append(f"타이포스쿼팅 의심: {target_domain}이(가) {search_domains[0]}과 유사함 (+{score})")
            metadata["closest_match"] = search_domains[0]
            
        elif match_type == "mismatch":
            # ⚠️ 불일치: 검색 결과에 없음
            reasons.append(f"도메인 불일치: {target_domain}이(가) '{keyword}' 검색 결과에 없음 (+{score})")
        
        return PhaseResult(
            phase="Phase 4: Search Verification",
            score=score,
            reasons=reasons,
            should_block=False,
            skip_remaining=False,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"❌ 검색 검증 실패: {e}")
        return PhaseResult(
            phase="Phase 4: Search Verification",
            score=0,
            reasons=["검색 검증 오류 - 단계 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": str(e)}
        )
