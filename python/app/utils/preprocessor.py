"""
HTML Preprocessor for Claude AI token optimization.
Removes unnecessary tags and extracts essential text content.
"""

from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Tags to completely remove from HTML
REMOVE_TAGS = [
    "script", "style", "svg", "path", "iframe", "img", 
    "noscript", "link", "meta", "head", "footer", "nav"
]


def preprocess_html(html_content: str, max_length: int = 8000) -> str:
    """
    Preprocess HTML content for AI analysis.
    Removes unnecessary tags and extracts essential text.
    
    Args:
        html_content: Raw HTML content
        max_length: Maximum length of output text
        
    Returns:
        Cleaned text suitable for AI analysis
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove unwanted tags completely
        for tag_name in REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Extract meta description
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag.get("content", "")
        
        # Extract body text
        body_text = ""
        body = soup.find("body")
        if body:
            body_text = body.get_text(separator=" ", strip=True)
        else:
            body_text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        body_text = " ".join(body_text.split())
        
        # Combine all extracted content
        combined = []
        if title:
            combined.append(f"[TITLE]: {title}")
        if meta_description:
            combined.append(f"[META]: {meta_description}")
        if body_text:
            combined.append(f"[CONTENT]: {body_text}")
        
        result = "\n".join(combined)
        
        # Truncate if too long
        if len(result) > max_length:
            result = result[:max_length] + "... [TRUNCATED]"
        
        return result
        
    except Exception as e:
        logger.error(f"HTML preprocessing failed: {e}")
        return ""


def extract_links(html_content: str) -> list[str]:
    """
    Extract all href links from HTML content.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        List of extracted URLs
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        links = []
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "")
            if href and href.startswith(("http://", "https://")):
                links.append(href)
        
        return links
        
    except Exception as e:
        logger.error(f"Link extraction failed: {e}")
        return []
