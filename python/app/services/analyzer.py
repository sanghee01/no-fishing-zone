"""
Main Analysis Pipeline Orchestrator.
Coordinates all phases and calculates final risk assessment.
"""

import logging
from typing import Tuple

from app.config import BLOCK_THRESHOLD, WARNING_THRESHOLD
from app.models import AnalyzeRequest, AnalyzeResponse, PhaseResult
from app.services.whitelist import check_whitelist
from app.services.redirect import track_redirects
from app.services.metadata import analyze_metadata
from app.services.ai_analyzer import analyze_with_ai
from app.services.search_verifier import verify_with_search

logger = logging.getLogger(__name__)


def determine_status(score: int) -> str:
    """
    Determine final status based on total risk score.
    
    Args:
        score: Total risk score
        
    Returns:
        Status string: SAFE, WARNING, or BLOCK
    """
    if score >= BLOCK_THRESHOLD:
        return "BLOCK"
    elif score >= WARNING_THRESHOLD:
        return "WARNING"
    return "SAFE"


async def analyze_url(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Main analysis pipeline orchestrator.
    Executes Phase 0-4 sequentially with proper error handling.
    
    Args:
        request: Analysis request containing URL and request ID
        
    Returns:
        AnalyzeResponse with final risk assessment
    """
    url = request.url
    total_score = 0
    all_reasons = []
    category = ""
    keyword = ""
    
    logger.info(f"[{request.request_id}] Starting analysis for: {url}")
    
    # ===== Phase 0: Whitelist Check =====
    try:
        phase0_result = check_whitelist(url)
        total_score += phase0_result.score
        all_reasons.extend(phase0_result.reasons)
        
        if phase0_result.skip_remaining:
            logger.info(f"[{request.request_id}] Whitelisted - returning SAFE")
            return AnalyzeResponse(
                url=url,
                status="SAFE",
                risk_score=0,
                category="Trusted",
                keyword="",
                reasons=all_reasons
            )
    except Exception as e:
        logger.error(f"[{request.request_id}] Phase 0 error: {e}")
        all_reasons.append("Phase 0: Error - skipped")
    
    # ===== Phase 1: Redirect Tracking =====
    html_content = None
    final_url = url
    
    try:
        phase1_result, final_url, html_content = await track_redirects(url)
        total_score += phase1_result.score
        all_reasons.extend(phase1_result.reasons)
        
        if phase1_result.should_block:
            logger.warning(f"[{request.request_id}] Blocked at Phase 1 - redirect loop")
            return AnalyzeResponse(
                url=url,
                status="BLOCK",
                risk_score=100,
                category="Malicious",
                keyword="",
                reasons=all_reasons
            )
    except Exception as e:
        logger.error(f"[{request.request_id}] Phase 1 error: {e}")
        all_reasons.append("Phase 1: Error - skipped")
    
    # ===== Phase 2: Metadata Analysis =====
    try:
        phase2_result = analyze_metadata(final_url)
        total_score += phase2_result.score
        all_reasons.extend(phase2_result.reasons)
    except Exception as e:
        logger.error(f"[{request.request_id}] Phase 2 error: {e}")
        all_reasons.append("Phase 2: Error - skipped")
    
    # ===== Phase 3: AI Analysis =====
    try:
        phase3_result = await analyze_with_ai(html_content)
        total_score += phase3_result.score
        all_reasons.extend(phase3_result.reasons)
        
        # Extract keyword and category from AI analysis
        keyword = phase3_result.metadata.get("keyword", "")
        category = phase3_result.metadata.get("category", "Common")
        
        if phase3_result.should_block:
            # Negative category - skip Phase 4 and return
            logger.warning(f"[{request.request_id}] Blocked at Phase 3 - Negative content")
            return AnalyzeResponse(
                url=url,
                status="BLOCK",
                risk_score=total_score,
                category=category,
                keyword=keyword,
                reasons=all_reasons
            )
    except Exception as e:
        logger.error(f"[{request.request_id}] Phase 3 error: {e}")
        all_reasons.append("Phase 3: Error - skipped")
    
    # ===== Phase 4: Search Verification =====
    # Only run for "Common" category (potential brand impersonation)
    if category == "Common" and keyword:
        try:
            phase4_result = await verify_with_search(final_url, keyword)
            total_score += phase4_result.score
            all_reasons.extend(phase4_result.reasons)
        except Exception as e:
            logger.error(f"[{request.request_id}] Phase 4 error: {e}")
            all_reasons.append("Phase 4: Error - skipped")
    
    # ===== Final Assessment =====
    status = determine_status(total_score)
    
    logger.info(f"[{request.request_id}] Analysis complete: {status} (score: {total_score})")
    
    return AnalyzeResponse(
        url=url,
        status=status,
        risk_score=total_score,
        category=category if category else "Unknown",
        keyword=keyword,
        reasons=all_reasons
    )
