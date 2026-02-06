"""
===========================================
📄 assess_model.py - 모델 성능 평가 스크립트
===========================================
OpenPhish + Tranco 데이터셋을 사용해 react-ai의 탐지 정확도를 측정합니다.

★ PhishTank 대신 OpenPhish 사용 (더 실시간, Dead URL 적음)

사용법:
    uv run python assess_model.py --limit 150

출력:
    - 4×2 혼동 행렬 (BLOCK/WARNING/SAFE × 악성/정상)
    - Detection Rate, Miss Rate, Block Precision
"""

import asyncio
import argparse
import json
import random
from pathlib import Path

import httpx

# ============================================
# 설정값
# ============================================
import os
REACT_AI_URL = os.getenv("REACT_AI_URL", "http://ai:8001")  # Docker: ai, 로컬: localhost


def load_openphish_samples(seeds_dir: Path, limit: int = 100) -> list[str]:
    """
    OpenPhish TXT에서 피싱 URL 샘플을 가져옵니다.
    
    OpenPhish 형식: 줄 단위 URL 목록
    https://example.com/phishing1
    https://example.com/phishing2
    ...
    
    ★ PhishTank보다 Dead URL이 적고, 12시간마다 갱신됨
    """
    txt_file = seeds_dir / "openphish.txt"
    
    if not txt_file.exists():
        print(f"⚠️ 파일 없음: {txt_file}")
        print(f"💡 'uv run python update_openphish.py'로 먼저 다운로드하세요.")
        return []
    
    print(f"[OpenPhish] 악성 URL {limit}개 로드 중...")
    
    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            all_urls = [
                line.strip() 
                for line in f 
                if line.strip() and line.strip().startswith("http")
            ]
        
        # 랜덤 샘플링
        samples = random.sample(all_urls, min(limit, len(all_urls)))
        print(f"[OpenPhish] ✅ {len(samples)}개 URL 샘플링 (전체: {len(all_urls)}개)")
        return samples
        
    except Exception as e:
        print(f"[OpenPhish] ❌ 로드 실패: {e}")
        return []


def load_tranco_samples(seeds_dir: Path, limit: int = 100) -> list[str]:
    """Tranco 화이트리스트에서 랜덤 샘플을 가져옵니다."""
    csv_file = seeds_dir / "1000000white.csv"
    
    if not csv_file.exists():
        print(f"⚠️ 파일 없음: {csv_file}")
        return []
    
    print(f"[Tranco] 정상 URL {limit}개 로드 중...")
    
    domains = []
    with open(csv_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                domains.append(f"https://{parts[1]}")
    
    samples = random.sample(domains, min(limit, len(domains)))
    print(f"[Tranco] ✅ {len(samples)}개 URL 샘플링 (전체: {len(domains)}개)")
    return samples


async def analyze_url(url: str) -> dict | None:
    """react-ai 서버에 분석 요청"""
    import uuid
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{REACT_AI_URL}/analyze",
                json={
                    "url": url,
                    "request_id": str(uuid.uuid4())  # 필수 필드
                }
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            pass
    return None


async def evaluate_model(
    malicious_urls: list[str],
    benign_urls: list[str]
) -> dict:
    """
    모델 성능을 평가합니다.
    
    4×2 혼동 행렬:
    - 예측: BLOCK, WARNING, SAFE
    - 실제: 악성, 정상
    """
    print("\n" + "=" * 50)
    print("🧪 모델 성능 평가 시작")
    print("=" * 50)
    
    # 4×2 혼동 행렬 초기화
    matrix = {
        "malicious": {"BLOCK": 0, "WARNING": 0, "SAFE": 0, "FAIL": 0},
        "benign": {"BLOCK": 0, "WARNING": 0, "SAFE": 0, "FAIL": 0}
    }
    
    # 악성 URL 테스트
    print(f"\n[Test] 악성 URL {len(malicious_urls)}개 테스트 중...")
    for i, url in enumerate(malicious_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status in matrix["malicious"]:
                matrix["malicious"][status] += 1
            else:
                matrix["malicious"]["SAFE"] += 1
        else:
            matrix["malicious"]["FAIL"] += 1
        
        if (i + 1) % 10 == 0:
            print(f"  진행: {i + 1}/{len(malicious_urls)}")
    
    # 정상 URL 테스트
    print(f"\n[Test] 정상 URL {len(benign_urls)}개 테스트 중...")
    for i, url in enumerate(benign_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status in matrix["benign"]:
                matrix["benign"][status] += 1
            else:
                matrix["benign"]["SAFE"] += 1
        else:
            matrix["benign"]["FAIL"] += 1
        
        if (i + 1) % 10 == 0:
            print(f"  진행: {i + 1}/{len(benign_urls)}")
    
    # 지표 계산
    m = matrix["malicious"]
    b = matrix["benign"]
    
    # Detection Rate: 악성을 BLOCK 또는 WARNING으로 탐지한 비율
    total_malicious = sum(m.values()) - m["FAIL"]
    detected = m["BLOCK"] + m["WARNING"]
    detection_rate = detected / total_malicious if total_malicious > 0 else 0
    
    # Miss Rate: 악성을 SAFE로 판정한 비율
    miss_rate = m["SAFE"] / total_malicious if total_malicious > 0 else 0
    
    # Block Precision: BLOCK 중 실제 악성 비율
    total_blocked = m["BLOCK"] + b["BLOCK"]
    block_precision = m["BLOCK"] / total_blocked if total_blocked > 0 else 0
    
    # False Block Rate: 정상을 BLOCK으로 판정한 비율
    total_benign = sum(b.values()) - b["FAIL"]
    false_block_rate = b["BLOCK"] / total_benign if total_benign > 0 else 0
    
    return {
        "matrix": matrix,
        "metrics": {
            "detection_rate": round(detection_rate, 4),
            "miss_rate": round(miss_rate, 4),
            "block_precision": round(block_precision, 4),
            "false_block_rate": round(false_block_rate, 4)
        }
    }


def print_results(results: dict):
    """결과 출력"""
    print("\n" + "=" * 50)
    print("📊 4×2 혼동 행렬")
    print("=" * 50)
    
    m = results["matrix"]["malicious"]
    b = results["matrix"]["benign"]
    metrics = results["metrics"]
    
    print(f"""
┌──────────────────────────────────────────────────┐
│                 실제 클래스                        │
│              악성         정상                    │
├──────────────────────────────────────────────────┤
│ 예측  BLOCK    {m['BLOCK']:4}         {b['BLOCK']:4}                   │
│       WARNING  {m['WARNING']:4}         {b['WARNING']:4}                   │
│       SAFE     {m['SAFE']:4}         {b['SAFE']:4}                   │
│       FAIL     {m['FAIL']:4}         {b['FAIL']:4}                   │
└──────────────────────────────────────────────────┘

📈 성능 지표:
  • Detection Rate (탐지율): {metrics['detection_rate']:.1%}
    → 악성을 BLOCK 또는 WARNING으로 탐지
    
  • Miss Rate (미탐율): {metrics['miss_rate']:.1%}
    → 악성을 SAFE로 잘못 판정 (0%가 목표)
    
  • Block Precision (차단 정밀도): {metrics['block_precision']:.1%}
    → BLOCK 판정 중 실제 악성 비율
    
  • False Block Rate (오차단율): {metrics['false_block_rate']:.1%}
    → 정상을 BLOCK으로 잘못 판정 (0%가 목표)
""")


async def main():
    parser = argparse.ArgumentParser(description="React-AI 모델 성능 평가")
    parser.add_argument("--limit", type=int, default=150, help="각 카테고리 최대 URL 수")
    parser.add_argument("--seeds-dir", type=str, default="seeds", help="시드 디렉토리 경로")
    args = parser.parse_args()
    
    seeds_dir = Path(args.seeds_dir)
    
    # 테스트 데이터 로드
    malicious_urls = load_openphish_samples(seeds_dir, args.limit)
    benign_urls = load_tranco_samples(seeds_dir, args.limit)
    
    if not malicious_urls:
        print("❌ 악성 URL을 로드하지 못했습니다.")
        return
    
    if not benign_urls:
        print("❌ 정상 URL을 로드하지 못했습니다.")
        return
    
    # 평가 실행
    results = await evaluate_model(malicious_urls, benign_urls)
    
    # 결과 출력
    print_results(results)
    
    # 결과 저장
    output_file = Path("assessment_result.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 결과 저장됨: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
