"""
Domain utility functions.
Provides Apex domain extraction and URL normalization.
"""

import tldextract
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def extract_apex_domain(url: str) -> str:
    """
    Extract the apex (root) domain from a URL.
    
    Examples:
        https://www.shinhan.com/path -> shinhan.com
        https://sub.domain.example.co.kr -> example.co.kr
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Apex domain string
    """
    try:
        extracted = tldextract.extract(url)
        
        if extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return extracted.domain
        
    except Exception as e:
        logger.error(f"Domain extraction failed for {url}: {e}")
        return ""


def extract_tld(url: str) -> str:
    """
    Extract the top-level domain (TLD) from a URL.
    
    Examples:
        https://example.xyz -> xyz
        https://example.co.kr -> co.kr
    
    Args:
        url: URL to extract TLD from
        
    Returns:
        TLD string
    """
    try:
        extracted = tldextract.extract(url)
        return extracted.suffix
        
    except Exception as e:
        logger.error(f"TLD extraction failed for {url}: {e}")
        return ""


def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent processing.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    try:
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        parsed = urlparse(url)
        
        # Reconstruct with consistent formatting
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}"
        if parsed.path:
            normalized += parsed.path
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized
        
    except Exception as e:
        logger.error(f"URL normalization failed for {url}: {e}")
        return url


def get_full_domain(url: str) -> str:
    """
    Extract the full domain (including subdomains) from a URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Full domain including subdomains
    """
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        return parsed.netloc.lower()
        
    except Exception as e:
        logger.error(f"Full domain extraction failed for {url}: {e}")
        return ""
