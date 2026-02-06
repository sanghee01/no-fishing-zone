"""
===========================================
📄 config.py - 환경 설정 및 상수 정의
===========================================
이 파일은 프로젝트 전체에서 사용되는 설정값과 상수를 정의합니다.
.env 파일에서 환경 변수를 불러오고, 각 Phase에서 사용하는 
점수 체계와 임계값을 한 곳에서 관리합니다.
"""

import os  # 운영체제 환경 변수 접근용
from pathlib import Path  # 파일 경로 처리용
from dotenv import load_dotenv  # .env 파일 로드용

# ============================================
# 환경 변수 로드
# ============================================
# .env 파일에서 ANTHROPIC_API_KEY 등을 읽어옵니다
load_dotenv()

# ============================================
# 경로 설정
# ============================================
# BASE_DIR: 프로젝트 루트 디렉토리 (python/)
# DATA_DIR: 정적 데이터 디렉토리 (python/data/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ============================================
# API 키 설정
# ============================================
# Anthropic Claude API 키 (.env 파일에서 읽어옴)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ============================================
# 서버 설정
# ============================================
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")  # 모든 IP에서 접근 허용
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))  # 기본 포트 8000

# ============================================
# 최종 판정 임계값 (v3 - 2026-02-07 미탐지/오차단 최적화)
# ============================================
# 70점 이상 = BLOCK (차단) - 더 높여서 오차단 방지
# 20점 이상 = WARNING (경고) - 더 낮춰서 미탐지 방지
# 20점 미만 = SAFE (안전)
# 
# ★ 목표: 미탐지(SAFE) 및 오차단(BLOCK) 각각 0~1개
BLOCK_THRESHOLD = int(os.getenv("BLOCK_THRESHOLD", "65"))  # 65 → 70 (오차단 더 감소)
WARNING_THRESHOLD = int(os.getenv("WARNING_THRESHOLD", "20"))  # 25 → 20 (미탐지 더 감소)

# ============================================
# Phase 1: 리다이렉트 분석 설정
# ============================================
REDIRECT_SCORE_PER_HOP = 5  # 리다이렉트 1회당 +5점
MAX_REDIRECT_HOPS = 20  # 20회 초과시 무한루프로 간주하여 즉시 차단

# ============================================
# Phase 2: 도메인 메타데이터 분석 설정
# ============================================
NEW_DOMAIN_DAYS_THRESHOLD = 14  # 14일 이내 생성된 도메인은 "신규"로 판단
NEW_DOMAIN_SCORE = 10  # 15 → 10 (오차단 감소)
SUSPICIOUS_TLD_SCORE = 10  # 수상한 TLD +10점

# 피싱에 자주 악용되는 수상한 최상위 도메인(TLD) 목록
SUSPICIOUS_TLDS = {"xyz", "top", "pw", "icu", "loan", "cam", "club", "online", "site", "work"}

# ============================================
# Phase 3: AI 분석 설정 (v3 - AI 영향력 최대화)
# ============================================
# ★ AI 분석이 가장 결정적인 역할 (55점 = 거의 WARNING 임계값 도달)
AI_SCORE_MULTIPLIER = 55  # 45 → 55 (AI 최대 55점, 압도적 영향력)
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # Claude 4.5 Haiku

# ============================================
# Phase 4: 검색 엔진 검증 설정 (v3 - 오탐 최소화)
# ============================================
# ★ 검색 미매칭 페널티 최소화 (정상 사이트도 안 뜨는 경우 많음)
TYPOSQUATTING_SCORE = 50  # 타이포스쿼팅 +50점 (결정타)
MISMATCH_SCORE = 5  # 10 → 5 (검색 미매칭 페널티 최소화)
LEVENSHTEIN_THRESHOLD_MIN = 1
LEVENSHTEIN_THRESHOLD_MAX = 3

# ============================================
# HTTP 요청 설정
# ============================================
REQUEST_TIMEOUT = 10.0  # 외부 요청 타임아웃 (초)

# 검색 엔진 크롤링시 사용할 User-Agent (브라우저로 위장)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
