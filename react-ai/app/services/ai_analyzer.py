"""
===========================================
📄 ai_analyzer.py - Phase 3: Claude AI 시맨틱 분석
===========================================
이 파일은 분석 파이프라인의 네 번째 단계(Phase 3)를 담당합니다.

시맨틱 분석이란?
- 웹페이지의 "내용"을 이해하고 분석하는 것
- 단순 키워드 매칭이 아닌, 문맥을 이해하는 AI 분석

Claude Haiku 4.5를 사용하는 이유:
1. 빠른 응답 속도 (실시간 분석에 적합)
2. 저렴한 비용 (대량 요청 처리 가능)
3. 충분한 성능 (피싱 패턴 감지에 적합)

점수 체계:
- AI 위험도(0.0~1.0) × 55 = 최대 +55점

카테고리:
- "Negative": 불법 콘텐츠 (도박, 음란물) → Phase 4 건너뛰고 즉시 차단
- "Common": 일반 서비스 (금융, 쇼핑) → Phase 4에서 사칭 여부 확인

v4 개선: HTML 없을 때 URL-Only AI 분석 Fallback 추가
"""

import json  # JSON 파싱용
import logging  # 로그 기록용
from typing import Optional  # 타입 힌트용

from anthropic import Anthropic  # Claude API 클라이언트

from app.config import ANTHROPIC_API_KEY, AI_SCORE_MULTIPLIER, CLAUDE_MODEL
from app.models import PhaseResult, AIAnalysisResult  # 결과 모델
from app.utils.preprocessor import preprocess_html  # HTML 전처리

logger = logging.getLogger(__name__)

# ============================================
# Claude에게 보내는 시스템 프롬프트 (v3 - 강화된 피싱 탐지)
# ============================================
SYSTEM_PROMPT = """너는 사이버 보안 전문가야. 주어진 웹페이지 텍스트를 분석해서 다음 JSON 형식으로만 응답해.

응답 형식:
{
    "keyword": "페이지가 나타내는 브랜드/서비스명 (예: 신한은행, 네이버)",
    "risk_score": 0.0~1.0 사이의 위험도 점수,
    "category": "Common" 또는 "Negative",
    "description": "아래 형식을 반드시 따라서 작성"
}

★ description 작성 형식 (필수):
1. [판단 요약] - 한 줄로 전체 판단 요약
2. [위험 요소] - 발견된 위험 요소 나열 (없으면 "없음")
3. [안전 요소] - 발견된 안전 요소 나열 (없으면 "없음")

카테고리 기준:
- "Negative": 도박, 음란물, 불법 약물, 사기 등 명백히 불법적인 콘텐츠
- "Common": 금융, 쇼핑, 뉴스, 소셜미디어 등 일반적인 서비스 (사칭 가능성 있음)

★★★ 피싱 고위험 판단 기준 (반드시 적용) ★★★

1. 개발자 플랫폼 악용:
   - vercel.app, github.io, netlify.app, pages.dev 등에서 공식 서비스(Amazon, Apple, 은행 등) 사칭
   - → 즉시 risk_score: 0.9 이상

2. 피싱 키워드 포함:
   - URL/도메인에 "clone", "pending", "verify", "confirm", "update", "secure", "login" 포함
   - → risk_score: 0.7 이상

3. 수상한 TLD + 금융/쇼핑 사칭:
   - .cn, .xyz, .top, .pw, .icu, .club 등에서 Amazon, 은행, PayPal 등 사칭
   - → risk_score: 0.8 이상

4. 긴급성 강조:
   - "즉시 확인", "24시간 내", "계정 정지", "결제 실패" 등 긴급성 문구
   - → risk_score: 0.6 이상

5. 개인정보 요구:
   - 로그인, 카드번호, 비밀번호, OTP 입력 요구
   - → risk_score: 0.7 이상

위험도 점수 기준:
- 0.0~0.2: 완전히 정상적인 공식 사이트
- 0.3~0.5: 약간 의심스러운 요소 (비정상적 TLD 등)
- 0.6~0.8: 피싱 가능성 높음 (긴급성 강조, 개인정보 요구)
- 0.9~1.0: 명확한 피싱/사기 (공식 서비스 사칭, 가짜 로그인)

반드시 유효한 JSON만 응답하고 다른 텍스트는 포함하지 마."""

# ============================================
# URL-Only 분석용 시스템 프롬프트 (v4 - Recall 개선)
# ============================================
# HTML 콘텐츠 없이 URL만으로 분석할 때 사용
URL_ONLY_SYSTEM_PROMPT = """너는 사이버 보안 전문가야. 주어진 URL을 분석해서 피싱/스캠 가능성을 평가해.

응답 형식:
{
    "keyword": "URL이 사칭하는 것으로 보이는 브랜드명 (없으면 빈 문자열)",
    "risk_score": 0.0~1.0 사이의 위험도 점수,
    "category": "Common" 또는 "Negative",
    "description": "판단 근거"
}

★★★ URL 기반 고위험 패턴 (반드시 적용) ★★★

1. 개발자 플랫폼에서 브랜드 사칭:
   - "amazon-clone.vercel.app", "netflix-test.github.io" 등
   - → risk_score: 0.9 이상

2. 피싱 키워드 포함:
   - "pending", "approve", "verify", "confirm", "secure", "update", "login", "clone"
   - → risk_score: 0.7 이상

3. 수상한 TLD:
   - .xyz, .top, .pw, .icu, .club, .sbs, .yoga 등
   - → risk_score: 0.5 이상

4. 랜덤 문자열 도메인:
   - "ab123cd.com", "xyzqwert.xyz" 등 의미없는 문자열
   - → risk_score: 0.6 이상

5. 브랜드명 + 수상한 도메인:
   - "apple.secure-login.xyz", "paypal.verify.top" 등
   - → risk_score: 0.8 이상

반드시 유효한 JSON만 응답하고 다른 텍스트는 포함하지 마."""

async def analyze_with_ai(html_content: Optional[str]) -> PhaseResult:
    """
    Claude AI를 사용하여 웹페이지 콘텐츠를 분석합니다.
    
    Args:
        html_content: 분석할 HTML 내용 (Phase 1에서 가져온 것)
        
    Returns:
        PhaseResult: Phase 3 분석 결과
        - keyword: AI가 감지한 브랜드명 (Phase 4에서 사용)
        - category: Common/Negative
        - score: AI 위험도 × 30
        
    동작 원리:
    1. HTML 전처리 (불필요한 태그 제거 → 토큰 절약)
    2. Claude API 호출
    3. JSON 응답 파싱
    4. 점수 계산 및 결과 반환
    """
    # ============================================
    # 입력 검증
    # ============================================
    if not html_content:
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["HTML 내용 없음 - 단계 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": "No HTML content"}
        )
    
    if not ANTHROPIC_API_KEY:
        logger.error("❌ ANTHROPIC_API_KEY가 설정되지 않음")
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["API 키 미설정 - 단계 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": "API key missing"}
        )
    
    try:
        # ============================================
        # HTML 전처리 (토큰 비용 최적화의 핵심!)
        # ============================================
        # <script>, <style> 등 불필요한 태그를 제거하여
        # Claude에게 보내는 텍스트 양을 70~80% 줄임
        processed_text = preprocess_html(html_content)
        
        if not processed_text:
            return PhaseResult(
                phase="Phase 3: AI Analysis",
                score=0,
                reasons=["HTML 전처리 결과가 비어있음 - 단계 건너뜀"],
                should_block=False,
                skip_remaining=False,
                metadata={"error": "Empty processed content"}
            )
        
        # ============================================
        # Claude API 호출
        # ============================================
        # Anthropic 클라이언트 생성 (API 키 사용)
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # 메시지 생성 요청
        message = client.messages.create(
            model=CLAUDE_MODEL,  # claude-3-5-haiku-20241022
            max_tokens=500,  # 응답 최대 길이 (JSON이므로 적게 설정)
            system=SYSTEM_PROMPT,  # 위에서 정의한 역할 지시
            messages=[
                {
                    "role": "user",  # 사용자 역할
                    "content": f"다음 웹페이지 콘텐츠를 분석해줘:\n\n{processed_text}"
                }
            ]
        )
        
        # ============================================
        # 응답 파싱
        # ============================================
        # Claude의 응답에서 텍스트 부분 추출
        response_text = message.content[0].text.strip()
        
        # 마크다운 코드 블록 제거 (```json ... ``` 형태로 올 수 있음)
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # 첫 줄(```json)과 마지막 줄(```) 제거
            response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        # JSON 파싱
        ai_result = json.loads(response_text)
        
        # 결과 객체로 변환 (Pydantic이 타입 검증)
        analysis = AIAnalysisResult(
            keyword=ai_result.get("keyword", ""),
            risk_score=float(ai_result.get("risk_score", 0.0)),
            category=ai_result.get("category", "Common"),
            description=ai_result.get("description", "")
        )
        
        # ============================================
        # 점수 계산
        # ============================================
        # AI 위험도(0.0~1.0) × 30 = 최대 30점
        score = int(analysis.risk_score * AI_SCORE_MULTIPLIER)
        
        reasons = []
        if score > 0:
            reasons.append(f"AI 위험도 평가: {analysis.risk_score:.2f} (+{score})")
        
        if analysis.description:
            # 설명이 너무 길면 100자로 자름
            reasons.append(f"AI 분석: {analysis.description[:100]}")
        
        # ============================================
        # 카테고리별 분기 처리
        # ============================================
        # Negative(불법 콘텐츠): Phase 4 건너뛰고 즉시 차단
        skip_phase4 = analysis.category == "Negative"
        
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=score,
            reasons=reasons,
            should_block=skip_phase4,  # Negative면 즉시 차단
            skip_remaining=skip_phase4,  # Negative면 Phase 4 건너뜀
            metadata={
                "keyword": analysis.keyword,
                "risk_score": analysis.risk_score,
                "category": analysis.category,
                "description": analysis.description,
                "model": CLAUDE_MODEL
            }
        )
        
    except json.JSONDecodeError as e:
        # ============================================
        # JSON 파싱 실패
        # ============================================
        # AI가 가끔 잘못된 형식으로 응답할 수 있음
        logger.error(f"❌ AI 응답 JSON 파싱 실패: {e}")
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["AI 응답 파싱 실패 - 단계 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": f"JSON parse error: {str(e)}"}
        )
        
    except Exception as e:
        # ============================================
        # 기타 예외
        # ============================================
        logger.error(f"❌ AI 분석 실패: {e}")
        return PhaseResult(
            phase="Phase 3: AI Analysis",
            score=0,
            reasons=["AI 분석 오류 - 단계 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": str(e)}
        )


async def analyze_url_only(url: str) -> PhaseResult:
    """
    URL만으로 AI 분석을 수행합니다 (HTML 없을 때 Fallback).
    
    v4 개선: HTML 콘텐츠를 가져올 수 없는 경우에도 URL 패턴만으로
    피싱 가능성을 평가하여 Recall을 개선합니다.
    
    Args:
        url: 분석할 URL
        
    Returns:
        PhaseResult: URL 기반 AI 분석 결과
    """
    if not ANTHROPIC_API_KEY:
        return PhaseResult(
            phase="Phase 3: URL-Only AI Analysis",
            score=0,
            reasons=["API 키 미설정 - URL 분석 건너뜀"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": "API key missing"}
        )
    
    try:
        # Claude API 클라이언트 생성
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # URL 분석 요청
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=URL_ONLY_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"다음 URL을 분석해줘: {url}"}
            ]
        )
        
        # 응답 텍스트 추출
        response_text = message.content[0].text.strip()
        logger.debug(f"🔍 URL-Only AI 응답: {response_text[:200]}...")
        
        # JSON 파싱
        analysis = AIAnalysisResult(**json.loads(response_text))
        
        # 점수 계산 (AI_SCORE_MULTIPLIER의 70%만 적용 - URL만으로는 덜 확실)
        url_multiplier = int(AI_SCORE_MULTIPLIER * 0.7)  # 55 * 0.7 = 38.5 → 38
        score = int(analysis.risk_score * url_multiplier)
        
        reasons = [f"URL-Only AI 분석: 위험도 {analysis.risk_score:.2f} (+{score})"]
        
        if analysis.keyword:
            reasons.append(f"감지된 브랜드: {analysis.keyword}")
        
        if analysis.description:
            reasons.append(f"AI 분석: {analysis.description[:100]}")
        
        logger.info(f"✅ URL-Only AI 분석 완료: {url[:50]} → {score}점")
        
        return PhaseResult(
            phase="Phase 3: URL-Only AI Analysis",
            score=score,
            reasons=reasons,
            should_block=False,
            skip_remaining=False,
            metadata={
                "keyword": analysis.keyword,
                "risk_score": analysis.risk_score,
                "category": analysis.category,
                "description": analysis.description,
                "model": CLAUDE_MODEL,
                "url_only": True
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ URL-Only AI 응답 JSON 파싱 실패: {e}")
        return PhaseResult(
            phase="Phase 3: URL-Only AI Analysis",
            score=0,
            reasons=["URL 분석 응답 파싱 실패"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": f"JSON parse error: {str(e)}"}
        )
        
    except Exception as e:
        logger.error(f"❌ URL-Only AI 분석 실패: {e}")
        return PhaseResult(
            phase="Phase 3: URL-Only AI Analysis",
            score=0,
            reasons=["URL 분석 오류"],
            should_block=False,
            skip_remaining=False,
            metadata={"error": str(e)}
        )

