"""
===========================================
📄 final_assessment.py - 해커톤 최종 성능 평가
===========================================
600개 URL (악성 300 + 정상 300) 테스트 및 Precision/Recall/F1-Score 측정

평가 기준:
- 악성 URL: SAFE가 아니면 탐지 성공 (BLOCK, WARNING = True Positive)
- 정상 URL: BLOCK이 아니면 정상 판정 (SAFE, WARNING = True Negative)
- DEAD: 통계에서 제외

사용법:
    docker compose exec search-ai uv run python final_assessment.py
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


def load_openphish_samples(limit: int = 300) -> list[str]:
    """OpenPhish에서 악성 URL 샘플 로드"""
    txt_file = SEEDS_DIR / "openphish.txt"
    if not txt_file.exists():
        print(f"⚠️ 파일 없음: {txt_file}")
        return []
    
    with open(txt_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]
    
    samples = random.sample(urls, min(limit, len(urls)))
    print(f"[OpenPhish] ✅ {len(samples)}개 악성 URL 로드")
    return samples


def load_tranco_samples(limit: int = 300) -> list[str]:
    """Tranco에서 정상 URL 샘플 로드"""
    csv_file = SEEDS_DIR / "1000000white.csv"
    if not csv_file.exists():
        print(f"⚠️ 파일 없음: {csv_file}")
        return []
    
    domains = []
    with open(csv_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                domains.append(f"https://{parts[1]}")
    
    samples = random.sample(domains, min(limit, len(domains)))
    print(f"[Tranco] ✅ {len(samples)}개 정상 URL 로드")
    return samples


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


async def run_final_assessment(limit: int = 300):
    """최종 성능 평가 실행"""
    
    # 샘플 로드
    malicious_urls = load_openphish_samples(limit)
    benign_urls = load_tranco_samples(limit)
    
    print("\n" + "=" * 70)
    print("🧪 Aegis Link AI 최종 성능 평가")
    print(f"   악성 URL: {len(malicious_urls)}개 (OpenPhish)")
    print(f"   정상 URL: {len(benign_urls)}개 (Tranco Top 1M)")
    print("=" * 70)
    
    # 4×2 혼동 행렬 초기화
    matrix = {
        "malicious": {"BLOCK": 0, "WARNING": 0, "SAFE": 0, "DEAD": 0},
        "benign": {"BLOCK": 0, "WARNING": 0, "SAFE": 0, "DEAD": 0}
    }
    
    # 악성 URL 테스트
    print(f"\n[Phase 1/2] 악성 URL {len(malicious_urls)}개 테스트 중...")
    for i, url in enumerate(malicious_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status in matrix["malicious"]:
                matrix["malicious"][status] += 1
            else:
                matrix["malicious"]["SAFE"] += 1
        else:
            matrix["malicious"]["DEAD"] += 1
        
        if (i + 1) % 50 == 0:
            print(f"  진행: {i + 1}/{len(malicious_urls)}")
    
    # 정상 URL 테스트
    print(f"\n[Phase 2/2] 정상 URL {len(benign_urls)}개 테스트 중...")
    for i, url in enumerate(benign_urls):
        result = await analyze_url(url)
        if result:
            status = result.get("status", "SAFE").upper()
            if status in matrix["benign"]:
                matrix["benign"][status] += 1
            else:
                matrix["benign"]["SAFE"] += 1
        else:
            matrix["benign"]["DEAD"] += 1
        
        if (i + 1) % 50 == 0:
            print(f"  진행: {i + 1}/{len(benign_urls)}")
    
    # DEAD 제외한 통계용 카운트
    m = matrix["malicious"]
    b = matrix["benign"]
    
    # 악성: DEAD 제외
    mal_total = m["BLOCK"] + m["WARNING"] + m["SAFE"]
    mal_detected = m["BLOCK"] + m["WARNING"]  # SAFE가 아니면 탐지 성공
    mal_missed = m["SAFE"]  # SAFE = 미탐지
    
    # 정상: DEAD 제외
    ben_total = b["BLOCK"] + b["WARNING"] + b["SAFE"]
    ben_correct = b["WARNING"] + b["SAFE"]  # BLOCK이 아니면 정상 판정
    ben_blocked = b["BLOCK"]  # BLOCK = 오차단
    
    # Precision, Recall, F1-Score 계산
    # TP: 악성을 BLOCK/WARNING으로 탐지
    # FP: 정상을 BLOCK으로 오차단
    # FN: 악성을 SAFE로 미탐지
    # TN: 정상을 WARNING/SAFE로 정상 판정
    
    TP = mal_detected
    FP = ben_blocked
    FN = mal_missed
    TN = ben_correct
    
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # 결과 저장
    result = {
        "test_info": {
            "total_urls": len(malicious_urls) + len(benign_urls),
            "malicious_urls": len(malicious_urls),
            "benign_urls": len(benign_urls),
            "malicious_source": "OpenPhish",
            "benign_source": "Tranco Top 1M"
        },
        "confusion_matrix": {
            "malicious": m,
            "benign": b
        },
        "statistics": {
            "malicious_total_excluding_dead": mal_total,
            "malicious_detected": mal_detected,
            "malicious_missed": mal_missed,
            "benign_total_excluding_dead": ben_total,
            "benign_correct": ben_correct,
            "benign_blocked": ben_blocked
        },
        "metrics": {
            "TP": TP,
            "FP": FP,
            "FN": FN,
            "TN": TN,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "detection_rate": round(mal_detected / mal_total, 4) if mal_total > 0 else 0,
            "false_positive_rate": round(ben_blocked / ben_total, 4) if ben_total > 0 else 0
        }
    }
    
    # JSON 저장
    with open("/app/final_assessment_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 결과 출력
    print("\n" + "=" * 70)
    print("📊 4×2 혼동 행렬 (DEAD 제외)")
    print("=" * 70)
    print(f"{'':15} {'BLOCK':>10} {'WARNING':>10} {'SAFE':>10} {'DEAD':>10}")
    print("-" * 55)
    print(f"{'악성 (Malicious)':15} {m['BLOCK']:>10} {m['WARNING']:>10} {m['SAFE']:>10} {m['DEAD']:>10}")
    print(f"{'정상 (Benign)':15} {b['BLOCK']:>10} {b['WARNING']:>10} {b['SAFE']:>10} {b['DEAD']:>10}")
    
    print("\n" + "=" * 70)
    print("📈 성능 지표 (Precision / Recall / F1-Score)")
    print("=" * 70)
    print(f"  True Positive (TP):  {TP:>5} (악성 → BLOCK/WARNING)")
    print(f"  False Positive (FP): {FP:>5} (정상 → BLOCK)")
    print(f"  False Negative (FN): {FN:>5} (악성 → SAFE)")
    print(f"  True Negative (TN):  {TN:>5} (정상 → WARNING/SAFE)")
    print("-" * 55)
    print(f"  Precision:           {precision:.4f} ({precision*100:.1f}%)")
    print(f"  Recall:              {recall:.4f} ({recall*100:.1f}%)")
    print(f"  F1-Score:            {f1_score:.4f} ({f1_score*100:.1f}%)")
    
    print("\n" + "=" * 70)
    print("📁 결과 저장: /app/final_assessment_result.json")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis Link AI 최종 성능 평가")
    parser.add_argument("--limit", type=int, default=300, help="각 카테고리 URL 개수 (기본: 300)")
    args = parser.parse_args()
    
    asyncio.run(run_final_assessment(args.limit))
