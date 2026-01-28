"""
Phase 0: Whitelist Filtering Service.
Provides fast pre-filtering using a trusted domain list.
"""

import logging
from pathlib import Path
from typing import Set, Optional

from app.config import DATA_DIR
from app.models import PhaseResult
from app.utils.domain import extract_apex_domain

logger = logging.getLogger(__name__)

# Global whitelist set (loaded once at startup)
_whitelist: Optional[Set[str]] = None


def load_whitelist() -> Set[str]:
    """
    Load whitelist domains from file into memory.
    Called once at application startup.
    """
    global _whitelist
    
    if _whitelist is not None:
        return _whitelist
    
    whitelist_path = DATA_DIR / "whitelist.txt"
    _whitelist = set()
    
    try:
        if whitelist_path.exists():
            with open(whitelist_path, "r", encoding="utf-8") as f:
                for line in f:
                    domain = line.strip().lower()
                    if domain and not domain.startswith("#"):
                        _whitelist.add(domain)
            
            logger.info(f"Loaded {len(_whitelist)} domains into whitelist")
        else:
            logger.warning(f"Whitelist file not found: {whitelist_path}")
            
    except Exception as e:
        logger.error(f"Failed to load whitelist: {e}")
    
    return _whitelist


def check_whitelist(url: str) -> PhaseResult:
    """
    Check if URL's apex domain is in the whitelist.
    
    Args:
        url: URL to check
        
    Returns:
        PhaseResult indicating if URL is whitelisted
    """
    whitelist = load_whitelist()
    apex_domain = extract_apex_domain(url).lower()
    
    if apex_domain in whitelist:
        return PhaseResult(
            phase="Phase 0: Whitelist",
            score=0,
            reasons=[f"Trusted domain: {apex_domain}"],
            should_block=False,
            skip_remaining=True,  # Skip all remaining phases
            metadata={"whitelisted": True, "apex_domain": apex_domain}
        )
    
    return PhaseResult(
        phase="Phase 0: Whitelist",
        score=0,
        reasons=[],
        should_block=False,
        skip_remaining=False,
        metadata={"whitelisted": False, "apex_domain": apex_domain}
    )
