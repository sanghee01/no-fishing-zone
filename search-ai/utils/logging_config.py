"""
===========================================
📄 logging_config.py - 로깅 설정
===========================================
Search-AI 크롤러의 로깅 시스템을 설정합니다.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    """
    로깅 시스템을 초기화합니다.
    
    - 콘솔 출력: INFO 레벨 이상
    - 파일 출력: DEBUG 레벨 이상 (logs/ 폴더)
    
    Args:
        log_dir: 로그 파일 저장 디렉토리 (기본: ./logs)
        
    Returns:
        설정된 Logger 인스턴스
    """
    # 로그 디렉토리 설정
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로그 파일명 (날짜별)
    log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 로거 생성
    logger = logging.getLogger("search-ai")
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷터 정의
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 콘솔 핸들러 (INFO 이상)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (DEBUG 이상)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"📝 로그 파일: {log_file}")
    
    return logger


# 모듈 임포트 시 기본 로거 생성
def get_logger() -> logging.Logger:
    """
    Search-AI 로거 인스턴스를 반환합니다.
    
    Returns:
        Logger 인스턴스
    """
    logger = logging.getLogger("search-ai")
    if not logger.handlers:
        setup_logging()
    return logger
