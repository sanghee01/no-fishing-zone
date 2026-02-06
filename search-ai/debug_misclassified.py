"""
===========================================
📄 debug_misclassified.py - 오차단/미탐지 URL 분석
===========================================
오차단된 정상 URL과 미탐지된 악성 URL을 상세히 출력합니다.

사용법:
    docker compose exec search-ai uv run python debug_misclassified.py --limit 30
"""

import asyncio
import argparse
import uuid
import random
from pathlib import Path

import httpx
import os

REACT_AI_URL = os.getenv("REACT_AI_URL", "http://ai:8001")
SEEDS_DIR = Path(os.getenv("SEEDS_DIR", "/app/seeds"))


def load_openphish_samples(limit: int = 30) -> list[str]:
    """OpenPhish에서 악성 URL 샘플 로드"""
    txt_file = SEEDS_DIR / "openphish.txt"
    if not txt_file.exists():
        return []
    
    with open(txt_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]
    
    return random.sample(urls, min(limit, len(urls)))


def load_tranco_samples(limit: int = 30) -> list[str]:
    """Tranco에서 정상 URL 샘플 로드"""
    csv_file = SEEDS_DIR / "1000000white.csv"
    if not csv_file.exists():
        return []
    
    domains = []
    with open(csv_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                domains.append(f"https://{parts[1]}")
    
    return random.sample(domains, min(limit, len(domains)))


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


async def analyze_misclassified(limit: int = 30):
    """오차단/미탐지 URL 분석"""
    
    # 샘플 로드
    malicious_urls = load_openphish_samples(limit)
    benign_urls = load_tranco_samples(limit)
    
    print("=" * 70)
    print("🔍 오차단/미탐지 URL 상세 분석")
    print("=" * 70)
    
    # 결과 저장
    false_negatives = []  # 악성 → SAFE (미탐지)
    false_positives = []  # 정상 → BLOCK (오차단)
    
    # 악성 URL 테스트
    print(f"\n📌 악성 URL {len(malicious_urls)}개 분석 중...")
    for i, url in enumerate(malicious_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status == "SAFE":
                false_negatives.append({
                    "url": url,
                    "status": status,
                    "risk_score": result.get("risk_score", 0),
                    "reasons": result.get("reasons", []),
                    "phases": result.get("phases", [])
                })
        print(f"  [{i+1}/{len(malicious_urls)}] {url[:50]}... → {result.get('status', 'FAIL') if result else 'FAIL'}")
    
    # 정상 URL 테스트
    print(f"\n📌 정상 URL {len(benign_urls)}개 분석 중...")
    for i, url in enumerate(benign_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status == "BLOCK":
                false_positives.append({
                    "url": url,
                    "status": status,
                    "risk_score": result.get("risk_score", 0),
                    "reasons": result.get("reasons", []),
                    "phases": result.get("phases", [])
                })
        print(f"  [{i+1}/{len(benign_urls)}] {url[:50]}... → {result.get('status', 'FAIL') if result else 'FAIL'}")
    
    # 결과 출력
    print("\n" + "=" * 70)
    print(f"❌ 미탐지 (악성 → SAFE): {len(false_negatives)}개")
    print("=" * 70)
    
    for i, item in enumerate(false_negatives, 1):
        print(f"\n--- [{i}] 미탐지 ---")
        print(f"URL: {item['url']}")
        print(f"점수: {item['risk_score']}")
        print(f"판정 이유:")
        for phase in item.get("phases", []):
            phase_name = phase.get("phase", "?")
            phase_score = phase.get("score", 0)
            phase_reasons = phase.get("reasons", [])
            print(f"  • {phase_name}: +{phase_score}")
            for reason in phase_reasons:
                print(f"    └ {reason[:100]}")
    
    print("\n" + "=" * 70)
    print(f"❌ 오차단 (정상 → BLOCK): {len(false_positives)}개")
    print("=" * 70)
    
    for i, item in enumerate(false_positives, 1):
        print(f"\n--- [{i}] 오차단 ---")
        print(f"URL: {item['url']}")
        print(f"점수: {item['risk_score']}")
        print(f"판정 이유:")
        for phase in item.get("phases", []):
            phase_name = phase.get("phase", "?")
            phase_score = phase.get("score", 0)
            phase_reasons = phase.get("reasons", [])
            print(f"  • {phase_name}: +{phase_score}")
            for reason in phase_reasons:
                print(f"    └ {reason[:100]}")
    
    # 요약
    print("\n" + "=" * 70)
    print("📊 요약")
    print("=" * 70)
    print(f"  미탐지 (악성 → SAFE): {len(false_negatives)}/{len(malicious_urls)} ({100*len(false_negatives)/len(malicious_urls):.1f}%)")
    print(f"  오차단 (정상 → BLOCK): {len(false_positives)}/{len(benign_urls)} ({100*len(false_positives)/len(benign_urls):.1f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="오차단/미탐지 URL 분석")
    parser.add_argument("--limit", type=int, default=30, help="URL 개수")
    args = parser.parse_args()
    
    asyncio.run(analyze_misclassified(args.limit))
