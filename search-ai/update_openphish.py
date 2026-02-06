"""
===========================================
📄 update_openphish.py - OpenPhish 피드 자동 갱신
===========================================
OpenPhish의 실시간 피드를 다운로드하여 openphish.txt를 업데이트합니다.

특징:
- 12시간마다 업데이트되는 실시간 피드
- PhishTank보다 Dead URL 비율이 낮음
- 최대 300개 URL 유지

사용법:
    uv run python update_openphish.py          # 1회 업데이트
    uv run python update_openphish.py --loop   # 24시간 간격 자동 갱신
"""

import asyncio
import argparse
from pathlib import Path
from datetime import datetime

import httpx

# OpenPhish 공개 피드 URL
OPENPHISH_FEED_URL = "https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt"

# 저장 경로
SEEDS_DIR = Path(__file__).parent / "seeds"
OUTPUT_FILE = SEEDS_DIR / "openphish.txt"


async def fetch_openphish_feed() -> list[str]:
    """
    OpenPhish GitHub 피드에서 URL 목록을 가져옵니다.
    
    Returns:
        피싱 URL 목록
    """
    print(f"[OpenPhish] 🌐 피드 다운로드 중: {OPENPHISH_FEED_URL}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(OPENPHISH_FEED_URL)
            response.raise_for_status()
            
            # 줄 단위로 분리 (빈 줄 제외)
            urls = [
                line.strip() 
                for line in response.text.splitlines() 
                if line.strip() and line.strip().startswith("http")
            ]
            
            print(f"[OpenPhish] ✅ {len(urls)}개 URL 다운로드 완료")
            return urls
            
        except httpx.HTTPStatusError as e:
            print(f"[OpenPhish] ❌ HTTP 오류: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"[OpenPhish] ❌ 다운로드 실패: {e}")
            return []


def save_to_file(urls: list[str]) -> bool:
    """
    URL 목록을 파일에 저장합니다 (덮어쓰기).
    
    Args:
        urls: 저장할 URL 목록
        
    Returns:
        성공 여부
    """
    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[OpenPhish] 💾 저장 완료: {OUTPUT_FILE}")
        print(f"[OpenPhish] 📅 업데이트 시간: {timestamp}")
        return True
        
    except Exception as e:
        print(f"[OpenPhish] ❌ 저장 실패: {e}")
        return False


async def update_once():
    """1회 업데이트 실행"""
    urls = await fetch_openphish_feed()
    
    if urls:
        save_to_file(urls)
        return True
    else:
        print("[OpenPhish] ⚠️ URL을 가져오지 못했습니다.")
        return False


async def update_loop(interval_hours: int = 24):
    """
    지정된 간격으로 반복 업데이트합니다.
    
    Args:
        interval_hours: 업데이트 간격 (시간)
    """
    interval_seconds = interval_hours * 3600
    
    print(f"[OpenPhish] 🔄 자동 갱신 모드 시작 (간격: {interval_hours}시간)")
    
    while True:
        await update_once()
        
        print(f"[OpenPhish] ⏳ 다음 업데이트까지 {interval_hours}시간 대기...")
        await asyncio.sleep(interval_seconds)


async def main():
    parser = argparse.ArgumentParser(description="OpenPhish 피드 업데이트")
    parser.add_argument(
        "--loop", 
        action="store_true", 
        help="24시간 간격으로 자동 갱신"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=24, 
        help="자동 갱신 간격 (시간, 기본: 24)"
    )
    args = parser.parse_args()
    
    if args.loop:
        await update_loop(args.interval)
    else:
        await update_once()


if __name__ == "__main__":
    asyncio.run(main())
