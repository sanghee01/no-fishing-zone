"""
===========================================
📄 preprocessor.py - HTML 전처리 유틸리티
===========================================
이 파일은 Claude AI에 보내기 전에 HTML을 정리합니다.

왜 전처리가 필요한가?
1. 비용 절감: Claude API는 토큰(단어 수) 기반 과금
2. 정확도 향상: 불필요한 코드 제거하면 AI가 핵심에 집중
3. 속도 향상: 데이터 양이 줄어 응답 시간 단축

제거 대상:
- <script>: JavaScript 코드 (분석에 불필요)
- <style>: CSS 스타일 (분석에 불필요)
- <svg>, <path>: 아이콘/그래픽 (분석에 불필요)
- <iframe>: 외부 삽입 콘텐츠
- <img>: 이미지 태그

추출 대상:
- <title>: 페이지 제목
- <meta description>: 페이지 설명
- <body>: 본문 텍스트
"""

from bs4 import BeautifulSoup  # HTML 파싱 라이브러리
from typing import Optional  # 타입 힌트
import logging

logger = logging.getLogger(__name__)

# ============================================
# 제거할 태그 목록
# ============================================
# 이 태그들은 콘텐츠 분석에 불필요하므로 완전히 제거
REMOVE_TAGS = [
    "script",   # JavaScript 코드
    "style",    # CSS 스타일
    "svg",      # 벡터 그래픽
    "path",     # SVG 경로
    "iframe",   # 외부 프레임
    "img",      # 이미지
    "noscript", # JavaScript 비활성화 대체 콘텐츠
    "link",     # 외부 리소스 링크
    "meta",     # 메타 태그 (description은 따로 추출)
    "head",     # 헤더 영역
    "footer",   # 푸터 영역
    "nav"       # 네비게이션 영역
]


def preprocess_html(html_content: str, max_length: int = 8000) -> str:
    """
    HTML 콘텐츠를 AI 분석용으로 전처리합니다.
    
    Args:
        html_content: 원본 HTML 문자열
        max_length: 최대 출력 길이 (기본 8000자)
        
    Returns:
        str: 정리된 텍스트 (AI 입력용)
        
    동작 원리:
    1. BeautifulSoup으로 HTML 파싱
    2. 불필요한 태그들 제거
    3. title, meta description, body 텍스트 추출
    4. 공백 정리 및 길이 제한
    
    출력 형식:
    [TITLE]: 페이지 제목
    [META]: 페이지 설명
    [CONTENT]: 본문 텍스트...
    """
    try:
        # HTML 파싱 (html.parser는 Python 내장 파서)
        soup = BeautifulSoup(html_content, "html.parser")
        
        # ============================================
        # 1. 불필요한 태그 제거
        # ============================================
        # decompose(): 태그와 그 내용을 완전히 제거
        for tag_name in REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # ============================================
        # 2. 주요 정보 추출
        # ============================================
        
        # 제목(title) 추출
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)  # strip=True: 앞뒤 공백 제거
        
        # 메타 설명(meta description) 추출
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag.get("content", "")
        
        # 본문(body) 텍스트 추출
        body_text = ""
        body = soup.find("body")
        if body:
            # separator=" ": 태그 사이에 공백 삽입
            body_text = body.get_text(separator=" ", strip=True)
        else:
            # body가 없으면 전체에서 텍스트 추출
            body_text = soup.get_text(separator=" ", strip=True)
        
        # ============================================
        # 3. 공백 정리
        # ============================================
        # 연속된 공백을 하나로 합침
        body_text = " ".join(body_text.split())
        
        # ============================================
        # 4. 결과 조합
        # ============================================
        combined = []
        if title:
            combined.append(f"[TITLE]: {title}")
        if meta_description:
            combined.append(f"[META]: {meta_description}")
        if body_text:
            combined.append(f"[CONTENT]: {body_text}")
        
        result = "\n".join(combined)
        
        # ============================================
        # 5. 길이 제한
        # ============================================
        # 너무 길면 잘라서 토큰 비용 절감
        if len(result) > max_length:
            result = result[:max_length] + "... [TRUNCATED]"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ HTML 전처리 실패: {e}")
        return ""


def extract_links(html_content: str) -> list[str]:
    """
    HTML에서 모든 외부 링크를 추출합니다.
    
    Args:
        html_content: HTML 문자열
        
    Returns:
        list[str]: 추출된 URL 목록
        
    사용 예:
    - 페이지 내 링크 분석
    - 악성 리다이렉트 URL 탐지
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        links = []
        
        # 모든 <a> 태그에서 href 속성 추출
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href", "")
            
            # http로 시작하는 외부 링크만 수집
            if href and href.startswith(("http://", "https://")):
                links.append(href)
        
        return links
        
    except Exception as e:
        logger.error(f"❌ 링크 추출 실패: {e}")
        return []
