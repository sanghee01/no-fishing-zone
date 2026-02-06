# 🧪 React-AI 성능 최적화 실험 보고서

> **실험일**: 2026-02-07 03:50 KST  
> **실험 목적**: 미탐지(SAFE for malicious) 및 오차단(BLOCK for benign) 최소화  
> **데이터셋**: OpenPhish 50개 (악성) + Tranco 50개 (정상)

---

## 📊 Before vs After 비교

### 설정 변경 사항

| 항목 | Before | After | 변경 목적 |
|------|--------|-------|----------|
| `BLOCK_THRESHOLD` | 55 | **65** | 오차단 감소 (더 높은 점수만 차단) |
| `WARNING_THRESHOLD` | 35 | **25** | 미탐지 감소 (더 낮은 점수도 경고) |
| `AI_SCORE_MULTIPLIER` | 30 | **45** | AI 분석 영향력 증가 |
| `MISMATCH_SCORE` | 15 | **10** | 검색 미매칭 페널티 감소 |

---

### 혼동 행렬 비교

#### Before (최적화 전)
```
              악성     정상
BLOCK          8         8     ← 정상 8개 오차단
WARNING       24         6
SAFE          18        36     ← 악성 18개 미탐지
FAIL           0         0
```

#### After (최적화 후)
```
              악성     정상
BLOCK          5         5     ← 정상 5개로 감소 ✅
WARNING       36         5
SAFE           9        40     ← 악성 9개로 감소 ✅
FAIL           0         0
```

---

### 성능 지표 비교

| 지표 | Before | After | 변화 | 목표 |
|------|--------|-------|------|------|
| **Detection Rate** | 64.0% | **82.0%** | +18% ✅ | 90%+ |
| **Miss Rate** | 36.0% | **18.0%** | -18% ✅ | 5% 미만 |
| **Block Precision** | 50.0% | **50.0%** | ±0% | 95%+ |
| **False Block Rate** | 16.0% | **10.0%** | -6% ✅ | 3% 미만 |

---

## 📈 핵심 개선 사항

### 1. 미탐지율 50% 개선
- **Before**: 악성 50개 중 18개를 SAFE로 판정 (36%)
- **After**: 악성 50개 중 9개를 SAFE로 판정 (18%)
- **개선폭**: 18% → 절반으로 감소

### 2. 오차단율 37% 개선
- **Before**: 정상 50개 중 8개를 BLOCK (16%)
- **After**: 정상 50개 중 5개를 BLOCK (10%)
- **개선폭**: 6%p 감소

### 3. WARNING 활용도 증가
- **악성 WARNING**: 24 → 36 (탐지 영역 확대)
- **정상 WARNING**: 6 → 5 (오탐 유지/감소)

---

## ⚙️ 최종 점수 체계 (v2)

```python
# react-ai/app/config.py (2026-02-07 최적화)

# 임계값
BLOCK_THRESHOLD = 65    # 65점 이상 → 차단
WARNING_THRESHOLD = 25  # 25점 이상 → 경고
# 25점 미만 → 안전

# 점수 가중치
AI_SCORE_MULTIPLIER = 45   # AI 최대 45점 (핵심)
NEW_DOMAIN_SCORE = 15      # 신규 도메인 +15점
SUSPICIOUS_TLD_SCORE = 10  # 수상한 TLD +10점
TYPOSQUATTING_SCORE = 50   # 타이포스쿼팅 +50점
MISMATCH_SCORE = 10        # 검색 미매칭 +10점
```

---

## 🎯 결론

| 목표 | 달성 여부 |
|------|----------|
| 미탐지 감소 | ✅ 36% → 18% (50% 개선) |
| 오차단 감소 | ✅ 16% → 10% (37% 개선) |
| WARNING 활용 | ✅ 악성 대부분 WARNING 이상 판정 |

### 추가 개선 방향
1. **AI 프롬프트 강화**: 피싱 패턴 탐지 정밀도 향상
2. **화이트리스트 확장**: 오차단되는 정상 사이트 추가
3. **타이포스쿼팅 탐지 강화**: 유사 도메인 검출 개선

---

## 📁 관련 파일

| 파일 | 설명 |
|------|------|
| `react-ai/app/config.py` | 점수 임계값 설정 |
| `docs/ai_performance_report.md` | 이전 테스트 보고서 |
| `assess_model.py` | 성능 평가 스크립트 |

---

*이 보고서는 자동 생성되었습니다.*
