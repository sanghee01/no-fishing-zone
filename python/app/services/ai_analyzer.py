"""
Phase 3: AI Semantic Analysis Service.
Uses Claude Haiku 4.5 for content analysis and categorization.
"""

import json
import logging
from typing import Optional

from anthropic import Anthropic

from app.config import ANTHROPIC_API_KEY, AI_SCORE_MULTIPLIER, CLAUDE_MODEL
from app.models import PhaseResult, AIAnalysisResult
from app.utils.preprocessor import preprocess_html

logger = logging.getLogger(__name__)

# System prompt for Claude
SYSTEM_PROMPT = """너는 보안 전문가야. 주어진 웹페이지 텍스트를 분석해서 다음 JSON 형식으로만 응답해.

응답 형식:
{
    "keyword": "페이지가 나타내는 브랜드/서비스명 (예: 신한은행, 네이버)",
    "risk_score": 0.0~1.0 사이의 위험도 점수,
    "category": "Common" 또는 "Negative",
    "description": "위험하다고 판단한 구체적 근거"
}

카테고리 기준:
- "Negative": 도박, 음란물, 불법 약물, 사기 등 명백히 불법적인 콘텐츠
- "Common": 금융, 쇼핑, 뉴스, 소셜미디어 등 일반적인 서비스 (사칭 가능성 있음)

위험도 판단 기준:
- 0.0~0.3: 정상적인 콘텐츠
- 0.4~0.6: 의심스러운 요소 존재 (긴급성 강조, 개인정보 요구 등)
- 0.7~1.0: 명확한 피싱/스캠 징후 (가짜 로그인, 사기성 문구 등)

반드시 유효한 JSON만 응답하고 다른 텍스트는 포함하지 마."""


async def analyze_with_ai(html_content: Optional[str]) -> PhaseResult:
    """
    Analyze webpage content using Claude Haiku 4.5.
    
    Args:
        html_content: Raw HTML content to analyze
        
    Returns:
        PhaseResult with AI analysis results
    """
    if not html_content:
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["No HTML content available - phase skipped"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": "No HTML content"}
        )
    
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured")
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["API key not configured - phase skipped"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": "API key missing"}
        )
    
    try:
        # Preprocess HTML for token optimization
        processed_text = preprocess_html(html_content)
        
        if not processed_text:
            return PhaseResult(
                phase="Phase 3: AI Analysis",
                score=0,
                reasons=["HTML preprocessing returned empty content - phase skipped"],
                should_block=False,
                skip_remaining=False,
                metadata={"error": "Empty processed content"}
            )
        
        # Call Claude API
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"다음 웹페이지 콘텐츠를 분석해줘:\n\n{processed_text}"
                }
            ]
        )
        
        # Parse AI response
        response_text = message.content[0].text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        ai_result = json.loads(response_text)
        
        analysis = AIAnalysisResult(
            keyword=ai_result.get("keyword", ""),
            risk_score=float(ai_result.get("risk_score", 0.0)),
            category=ai_result.get("category", "Common"),
            description=ai_result.get("description", "")
        )
        
        # Calculate score (AI risk_score * multiplier)
        score = int(analysis.risk_score * AI_SCORE_MULTIPLIER)
        
        reasons = []
        if score > 0:
            reasons.append(f"AI risk assessment: {analysis.risk_score:.2f} (+{score})")
        if analysis.description:
            reasons.append(f"AI insight: {analysis.description[:100]}")
        
        # Determine if we should skip Phase 4
        skip_phase4 = analysis.category == "Negative"
        
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=score,
            reasons=reasons,
            should_block=skip_phase4,  # Block immediately for Negative content
            skip_remaining=skip_phase4,
            metadata={
                "keyword": analysis.keyword,
                "risk_score": analysis.risk_score,
                "category": analysis.category,
                "description": analysis.description,
                "model": CLAUDE_MODEL
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["AI response parsing failed - phase skipped"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": f"JSON parse error: {str(e)}"}
        )
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["AI analysis error - phase skipped"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": str(e)}
        )
