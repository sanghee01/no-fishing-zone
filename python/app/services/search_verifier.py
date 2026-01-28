"""
Phase 4: Search Engine Cross-Verification Service.
Verifies brand authenticity using Google and Naver search results.
"""

import httpx
import logging
from urllib.parse import quote
from typing import List, Tuple
from Levenshtein import distance as levenshtein_distance

from bs4 import BeautifulSoup

from app.config import (
    TYPOSQUATTING_SCORE,
    MISMATCH_SCORE,
    LEVENSHTEIN_THRESHOLD_MIN,
    LEVENSHTEIN_THRESHOLD_MAX,
    REQUEST_TIMEOUT,
    USER_AGENT
)
from app.models import PhaseResult
from app.utils.domain import extract_apex_domain

logger = logging.getLogger(__name__)

# Search engine URLs
NAVER_SEARCH_URL = "https://search.naver.com/search.naver?query={keyword}"
GOOGLE_SEARCH_URL = "https://www.google.com/search?q={keyword}"


async def fetch_search_results(keyword: str) -> List[str]:
    """
    Fetch top search results from Google and Naver.
    
    Args:
        keyword: Keyword to search for
        
    Returns:
        List of apex domains from top search results
    """
    domains = []
    encoded_keyword = quote(keyword)
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=headers) as client:
        # Search Naver
        try:
            naver_url = NAVER_SEARCH_URL.format(keyword=encoded_keyword)
            response = await client.get(naver_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract links from Naver search results
                for link in soup.select("a[href]"):
                    href = link.get("href", "")
                    if href.startswith("http") and "naver.com" not in href:
                        apex = extract_apex_domain(href)
                        if apex and apex not in domains:
                            domains.append(apex)
                            if len(domains) >= 5:
                                break
                                
        except Exception as e:
            logger.warning(f"Naver search failed: {e}")
        
        # Search Google
        try:
            google_url = GOOGLE_SEARCH_URL.format(keyword=encoded_keyword)
            response = await client.get(google_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract links from Google search results
                for link in soup.select("a[href]"):
                    href = link.get("href", "")
                    
                    # Google wraps URLs, extract actual URL
                    if "/url?q=" in href:
                        start = href.find("/url?q=") + 7
                        end = href.find("&", start)
                        if end == -1:
                            end = len(href)
                        href = href[start:end]
                    
                    if href.startswith("http") and "google.com" not in href:
                        apex = extract_apex_domain(href)
                        if apex and apex not in domains:
                            domains.append(apex)
                            if len(domains) >= 10:  # Get more for better coverage
                                break
                                
        except Exception as e:
            logger.warning(f"Google search failed: {e}")
    
    return domains[:5]  # Return top 5


def check_similarity(target_domain: str, search_domains: List[str]) -> Tuple[str, int]:
    """
    Check if target domain matches or is similar to search results.
    
    Args:
        target_domain: Domain being analyzed
        search_domains: Domains from search results
        
    Returns:
        Tuple of (match_type, score)
        match_type: "match", "similar", or "mismatch"
    """
    target_apex = extract_apex_domain(target_domain).lower()
    
    if not search_domains:
        # No search results to compare
        return ("unknown", 0)
    
    # Check for exact match first
    for domain in search_domains:
        if domain.lower() == target_apex:
            return ("match", 0)
    
    # Check for typosquatting (similar but not exact)
    min_distance = float("inf")
    closest_domain = ""
    
    for domain in search_domains:
        dist = levenshtein_distance(target_apex, domain.lower())
        if dist < min_distance:
            min_distance = dist
            closest_domain = domain
    
    # Typosquatting detection: very similar but not identical
    if LEVENSHTEIN_THRESHOLD_MIN <= min_distance <= LEVENSHTEIN_THRESHOLD_MAX:
        return ("similar", TYPOSQUATTING_SCORE)
    
    # No match found in top results
    return ("mismatch", MISMATCH_SCORE)


async def verify_with_search(url: str, keyword: str) -> PhaseResult:
    """
    Verify URL authenticity using search engine cross-verification.
    
    Args:
        url: URL being analyzed
        keyword: Brand/service keyword from AI analysis
        
    Returns:
        PhaseResult with verification results
    """
    if not keyword:
        return PhaseResult(
            phase="Phase 4: Search Verification",
            score=0,
            reasons=["No keyword for search - phase skipped"],
            should_block=False,
            skip_remaining=False,
            metadata={"skipped": True, "reason": "No keyword"}
        )
    
    try:
        # Get search results
        search_domains = await fetch_search_results(keyword)
        
        if not search_domains:
            return PhaseResult(
                phase="Phase 4: Search Verification",
                score=0,
                reasons=["No search results found - phase skipped"],
                should_block=False,
                skip_remaining=False,
                metadata={"skipped": True, "reason": "No search results"}
            )
        
        # Extract apex domain from URL
        target_domain = extract_apex_domain(url)
        
        # Check similarity
        match_type, score = check_similarity(target_domain, search_domains)
        
        reasons = []
        metadata = {
            "keyword": keyword,
            "target_domain": target_domain,
            "search_results": search_domains,
            "match_type": match_type
        }
        
        if match_type == "match":
            reasons.append(f"Domain verified: {target_domain} matches search results")
            
        elif match_type == "similar":
            reasons.append(f"Typosquatting detected: {target_domain} similar to {search_domains[0]} (+{score})")
            metadata["closest_match"] = search_domains[0]
            
        elif match_type == "mismatch":
            reasons.append(f"Domain mismatch: {target_domain} not in top search results for '{keyword}' (+{score})")
        
        return PhaseResult(
            phase="Phase 4: Search Verification",
            score=score,
            reasons=reasons,
            should_block=False,
            skip_remaining=False,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Search verification failed: {e}")
        return PhaseResult(
            phase="Phase 4: Search Verification",
            score=0,
            reasons=["Search verification error - phase skipped"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": str(e)}
        )
