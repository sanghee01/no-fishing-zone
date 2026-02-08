"""
===========================================
📄 analyze_false_negatives.py - 미탐지 URL 상세 분석
===========================================
악성 URL인데 SAFE로 판정된 URL들의 description을 분석합니다.

사용법:
    docker compose exec search-ai uv run python analyze_false_negatives.py --limit 50
"""

import asyncio
import argparse
import uuid
import random
import json
from pathlib import Path

import httpx
import os

REACT_AI_URL = os.getenv("REACT_AI_URL", "http://ai:8001")
SEEDS_DIR = Path(os.getenv("SEEDS_DIR", "/app/seeds"))


def load_openphish_samples(limit: int = 50) -> list[str]:
    """OpenPhish에서 악성 URL 샘플 로드"""
    txt_file = SEEDS_DIR / "openphish.txt"
    if not txt_file.exists():
        return []
    
    with open(txt_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]
    
    return random.sample(urls, min(limit, len(urls)))


async def analyze_url(url: str) -> dict | None:
    """react-ai 분석 요청"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{REACT_AI_URL}/analyze",
                json={"url": url, "request_id": str(uuid.uuid4())}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            pass
    return None


async def analyze_false_negatives(limit: int = 50):
    """미탐지(악성→SAFE) URL 상세 분석"""
    
    malicious_urls = load_openphish_samples(limit)
    
    print("=" * 80)
    print("🔍 미탐지 URL 상세 분석 (악성 → SAFE)")
    print("=" * 80)
    
    false_negatives = []
    
    for i, url in enumerate(malicious_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status == "SAFE":
                false_negatives.append({
                    "url": url,
                    "status": status,
                    "risk_score": result.get("risk_score", 0),
                    "ai_risk_score": result.get("ai_risk_score", 0),
                    "description": result.get("description", ""),
                    "keyword": result.get("keyword", ""),
                    "phases": result.get("phases", [])
                })
        
        if (i + 1) % 10 == 0:
            print(f"  진행: {i + 1}/{len(malicious_urls)}, 미탐지: {len(false_negatives)}개")
    
    # 결과 출력
    print("\n" + "=" * 80)
    print(f"❌ 미탐지 URL 상세 분석: {len(false_negatives)}/{len(malicious_urls)}개")
    print("=" * 80)
    
    # 패턴 분석을 위한 데이터 수집
    low_ai_score = []  # AI 점수가 낮은 경우
    common_keywords = {}  # 자주 등장하는 키워드
    common_patterns = []  # 공통 패턴
    
    for i, item in enumerate(false_negatives, 1):
        print(f"\n--- [{i}/{len(false_negatives)}] 미탐지 ---")
        print(f"URL: {item['url']}")
        print(f"위험 점수: {item['risk_score']}")
        print(f"AI 위험도: {item.get('ai_risk_score', 'N/A')}")
        print(f"키워드: {item['keyword']}")
        print(f"Description: {item['description'][:300]}..." if len(item['description']) > 300 else f"Description: {item['description']}")
        
        # 패턴 분석
        if item['risk_score'] < 20:
            low_ai_score.append(item)
        
        keyword = item.get('keyword', '')
        if keyword:
            common_keywords[keyword] = common_keywords.get(keyword, 0) + 1
    
    # 패턴 요약
    print("\n" + "=" * 80)
    print("📊 미탐지 패턴 분석")
    print("=" * 80)
    
    print(f"\n[1] 위험 점수 분포:")
    score_ranges = {"0-10": 0, "11-19": 0, "20+": 0}
    for item in false_negatives:
        score = item['risk_score']
        if score <= 10:
            score_ranges["0-10"] += 1
        elif score <= 19:
            score_ranges["11-19"] += 1
        else:
            score_ranges["20+"] += 1
    
    for range_name, count in score_ranges.items():
        print(f"  {range_name}점: {count}개")
    
    print(f"\n[2] 자주 등장하는 키워드 (Top 10):")
    sorted_keywords = sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    for keyword, count in sorted_keywords:
        print(f"  {keyword}: {count}회")
    
    # JSON 저장
    result = {
        "total_tested": len(malicious_urls),
        "false_negatives_count": len(false_negatives),
        "false_negative_rate": len(false_negatives) / len(malicious_urls) if malicious_urls else 0,
        "score_distribution": score_ranges,
        "common_keywords": dict(sorted_keywords),
        "false_negatives": false_negatives
    }
    
    with open("/app/false_negatives_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("📁 결과 저장: /app/false_negatives_analysis.json")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="미탐지 URL 상세 분석")
    parser.add_argument("--limit", type=int, default=50, help="테스트 URL 개수 (기본: 50)")
    args = parser.parse_args()
    
    asyncio.run(analyze_false_negatives(args.limit))
