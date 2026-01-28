"""
Phase 1: Redirect Tracking Service.
Tracks HTTP redirects and detects suspicious redirect chains.
"""

import httpx
import logging
from typing import Tuple, Optional

from app.config import (
    REDIRECT_SCORE_PER_HOP,
    MAX_REDIRECT_HOPS,
    REQUEST_TIMEOUT,
    USER_AGENT
)
from app.models import PhaseResult

logger = logging.getLogger(__name__)


async def track_redirects(url: str) -> Tuple[PhaseResult, str, Optional[str]]:
    """
    Track redirects and calculate risk score based on hop count.
    
    Args:
        url: URL to track redirects for
        
    Returns:
        Tuple of (PhaseResult, final_url, html_content)
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=MAX_REDIRECT_HOPS + 1,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(url)
            
            redirect_count = len(response.history)
            final_url = str(response.url)
            html_content = response.text
            
            # Check for infinite loop (exceeded max redirects)
            if redirect_count > MAX_REDIRECT_HOPS:
                return (
                    PhaseResult(
                        phase="Phase 1: Redirect",
                        score=100,  # Maximum score for immediate block
                        reasons=[f"Infinite redirect loop detected ({redirect_count} hops)"],
                        should_block=True,
                        skip_remaining=True,
                        metadata={
                            "redirect_count": redirect_count,
                            "final_url": final_url
                        }
                    ),
                    final_url,
                    None
                )
            
            # Calculate score based on redirect count
            score = redirect_count * REDIRECT_SCORE_PER_HOP
            reasons = []
            
            if redirect_count > 0:
                reasons.append(f"Redirect count: {redirect_count} (+{score})")
            
            return (
                PhaseResult(
                    phase="Phase 1: Redirect",
                    score=score,
                    reasons=reasons,
                    should_block=False,
                    skip_remaining=False,
                    metadata={
                        "redirect_count": redirect_count,
                        "final_url": final_url,
                        "status_code": response.status_code
                    }
                ),
                final_url,
                html_content
            )
            
    except httpx.TooManyRedirects:
        return (
            PhaseResult(
                phase="Phase 1: Redirect",
                score=100,
                reasons=["Exceeded maximum redirect limit (Hard Block)"],
                should_block=True,
                skip_remaining=True,
                metadata={"error": "TooManyRedirects"}
            ),
            url,
            None
        )
        
    except httpx.TimeoutException:
        logger.warning(f"Timeout while fetching {url}")
        return (
            PhaseResult(
                phase="Phase 1: Redirect",
                score=0,
                reasons=["Request timeout - phase skipped"],
                should_block=False,
                skip_remaining=False,
                metadata={"error": "Timeout"}
            ),
            url,
            None
        )
        
    except Exception as e:
        logger.error(f"Redirect tracking failed for {url}: {e}")
        return (
            PhaseResult(
                phase="Phase 1: Redirect",
                score=0,
                reasons=[f"Error occurred - phase skipped"],
                should_block=False,
                skip_remaining=False,
                metadata={"error": str(e)}
            ),
            url,
            None
        )
