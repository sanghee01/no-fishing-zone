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
# 최종 판정 임계값
# ============================================
# 60점 이상 = BLOCK (차단)
# 30~59점 = WARNING (경고)
# 30점 미만 = SAFE (안전)
BLOCK_THRESHOLD = int(os.getenv("BLOCK_THRESHOLD", "55"))  # 60 → 55 (WARNING→BLOCK 전환 유도)
WARNING_THRESHOLD = int(os.getenv("WARNING_THRESHOLD", "35"))  # 30 → 35 (오탐 감소)

# ============================================
# Phase 1: 리다이렉트 분석 설정
# ============================================
REDIRECT_SCORE_PER_HOP = 5  # 리다이렉트 1회당 +5점
MAX_REDIRECT_HOPS = 20  # 20회 초과시 무한루프로 간주하여 즉시 차단

# ============================================
# Phase 2: 도메인 메타데이터 분석 설정
# ============================================
NEW_DOMAIN_DAYS_THRESHOLD = 14  # 14일 이내 생성된 도메인은 "신규"로 판단
NEW_DOMAIN_SCORE = 15  # 신규 도메인 +15점
SUSPICIOUS_TLD_SCORE = 10  # 수상한 TLD +10점

# 피싱에 자주 악용되는 수상한 최상위 도메인(TLD) 목록
SUSPICIOUS_TLDS = {"xyz", "top", "pw", "icu", "loan", "cam", "club", "online", "site", "work"}

# ============================================
# Phase 3: AI 분석 설정
# ============================================
AI_SCORE_MULTIPLIER = 30  # AI 위험도(0.0~1.0)에 곱해서 점수화 (최대 30점)
CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # 사용할 Claude 모델 (Claude 4.5 Haiku 스테이블, 2025-10-01)

# ============================================
# Phase 4: 검색 엔진 검증 설정
# ============================================
TYPOSQUATTING_SCORE = 50  # 유사 도메인(타이포스쿼팅) 발견시 +50점 (결정타)
MISMATCH_SCORE = 15  # 검색 결과에 없는 경우 +15점 (30 → 15, 오탐 감소)
LEVENSHTEIN_THRESHOLD_MIN = 1  # 편집거리 최소값 (완전 일치는 0이므로 제외)
LEVENSHTEIN_THRESHOLD_MAX = 3  # 편집거리 최대값 (너무 다르면 타이포스쿼팅 아님)

# ============================================
# HTTP 요청 설정
# ============================================
REQUEST_TIMEOUT = 10.0  # 외부 요청 타임아웃 (초)

# 검색 엔진 크롤링시 사용할 User-Agent (브라우저로 위장)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
