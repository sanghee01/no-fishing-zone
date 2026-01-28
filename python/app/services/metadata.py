"""
Phase 2: Domain Metadata Analysis Service.
Analyzes WHOIS data and TLD for risk assessment.
"""

import whois
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import (
    NEW_DOMAIN_DAYS_THRESHOLD,
    NEW_DOMAIN_SCORE,
    SUSPICIOUS_TLD_SCORE,
    SUSPICIOUS_TLDS
)
from app.models import PhaseResult
from app.utils.domain import extract_apex_domain, extract_tld

logger = logging.getLogger(__name__)


def analyze_metadata(url: str) -> PhaseResult:
    """
    Analyze domain metadata including WHOIS and TLD.
    
    Args:
        url: URL to analyze
        
    Returns:
        PhaseResult with metadata analysis results
    """
    score = 0
    reasons = []
    metadata = {}
    
    apex_domain = extract_apex_domain(url)
    tld = extract_tld(url)
    
    metadata["apex_domain"] = apex_domain
    metadata["tld"] = tld
    
    # Check WHOIS for domain age
    try:
        domain_info = whois.whois(apex_domain)
        creation_date = domain_info.creation_date
        
        # Handle list of dates (some registrars return multiple)
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        
        if creation_date:
            # Make creation_date timezone-aware if it isn't
            if creation_date.tzinfo is None:
                creation_date = creation_date.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            domain_age_days = (now - creation_date).days
            
            metadata["creation_date"] = creation_date.isoformat()
            metadata["domain_age_days"] = domain_age_days
            
            if domain_age_days <= NEW_DOMAIN_DAYS_THRESHOLD:
                score += NEW_DOMAIN_SCORE
                reasons.append(f"New domain ({domain_age_days} days old) (+{NEW_DOMAIN_SCORE})")
                
    except Exception as e:
        logger.warning(f"WHOIS lookup failed for {apex_domain}: {e}")
        metadata["whois_error"] = str(e)
        # WHOIS failure = 0 points (as per spec)
    
    # Check for suspicious TLD
    tld_parts = tld.split(".")
    primary_tld = tld_parts[-1].lower() if tld_parts else ""
    
    if primary_tld in SUSPICIOUS_TLDS:
        score += SUSPICIOUS_TLD_SCORE
        reasons.append(f"Suspicious TLD: .{primary_tld} (+{SUSPICIOUS_TLD_SCORE})")
        metadata["suspicious_tld"] = True
    else:
        metadata["suspicious_tld"] = False
    
    return PhaseResult(
        phase="Phase 2: Metadata",
        score=score,
        reasons=reasons,
        should_block=False,
        skip_remaining=False,
        metadata=metadata
    )
