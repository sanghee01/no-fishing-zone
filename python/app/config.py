"""
Configuration module for the AI Analysis Server.
Loads environment variables and defines constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Analysis thresholds
BLOCK_THRESHOLD = int(os.getenv("BLOCK_THRESHOLD", "60"))
WARNING_THRESHOLD = int(os.getenv("WARNING_THRESHOLD", "30"))

# Phase 1: Redirect scoring
REDIRECT_SCORE_PER_HOP = 5
MAX_REDIRECT_HOPS = 20

# Phase 2: Domain metadata scoring
NEW_DOMAIN_DAYS_THRESHOLD = 14
NEW_DOMAIN_SCORE = 15
SUSPICIOUS_TLD_SCORE = 10
SUSPICIOUS_TLDS = {"xyz", "top", "pw", "icu", "loan", "cam", "club", "online", "site", "work"}

# Phase 3: AI analysis
AI_SCORE_MULTIPLIER = 30
CLAUDE_MODEL = "claude-3-5-haiku-20241022"

# Phase 4: Search verification scoring
TYPOSQUATTING_SCORE = 50
MISMATCH_SCORE = 30
LEVENSHTEIN_THRESHOLD_MIN = 1
LEVENSHTEIN_THRESHOLD_MAX = 3

# HTTP request configuration
REQUEST_TIMEOUT = 10.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
