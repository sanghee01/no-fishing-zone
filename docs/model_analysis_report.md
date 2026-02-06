# 🔬 React-AI 모델 성능 분석 보고서 v2

> **작성일**: 2026-02-06  
> **대상**: Aegis Link 팀원

---

## 📊 분류 체계

### 예측 클래스 (4개)
| 상태 | 점수 | 의미 |
|------|------|------|
| **BLOCK** | 60+ | 즉시 차단 (도박, 피싱 등) |
| **WARNING** | 35~59 | 주의 필요 (의심스러운 요소) |
| **SAFE** | 0~34 | 안전 판정 |
| **DEAD** | - | 접속 불가 (페이지 없음) |

### 실제 클래스 (2개)
| 라벨 | 설명 | 데이터 소스 |
|------|------|------------|
| **악성** | 피싱/도박/불법 | URLhaus, PhishTank |
| **정상** | 합법적 사이트 | Tranco Top 1M |

---

## 🎯 평가 기준

### 대회 목적의 엄격한 기준
**"악성은 반드시 BLOCK"**

| 실제 | 예측 | 결과 |
|------|------|------|
| 악성 | BLOCK | ✅ **정탐 (TP)** |
| 악성 | WARNING | ⚠️ **부분 정탐** |
| 악성 | SAFE | ❌ **미탐 (FN)** - 치명적 |
| 악성 | DEAD | ➖ 제외 (접속 불가) |
| 정상 | BLOCK | ❌ **심각한 오탐** |
| 정상 | WARNING | ⚠️ **경미한 오탐** |
| 정상 | SAFE | ✅ **정탐 (TN)** |
| 정상 | DEAD | ➖ 제외 (접속 불가) |

---

## 📈 핵심 지표

### 1. Block Precision (차단 정밀도)
```
Block Precision = 악성→BLOCK / (악성→BLOCK + 정상→BLOCK)
```
- **의미**: BLOCK 판정 중 실제 악성 비율
- **목표**: 95% 이상 (잘못된 차단 최소화)

### 2. Detection Rate (탐지율)
```
Detection Rate = (악성→BLOCK + 악성→WARNING) / 전체 악성
```
- **의미**: 악성을 최소 WARNING 이상으로 탐지한 비율
- **목표**: 90% 이상

### 3. Miss Rate (미탐율) ⚠️ 중요
```
Miss Rate = 악성→SAFE / 전체 악성
```
- **의미**: 악성을 SAFE로 잘못 판정한 비율
- **목표**: 5% 미만 (0에 가까울수록 좋음)

### 4. False Block Rate (오차단율)
```
False Block Rate = 정상→BLOCK / 전체 정상
```
- **의미**: 정상을 BLOCK으로 잘못 판정한 비율
- **목표**: 3% 미만

---

## 📋 4×2 혼동 행렬

```
                        실제 클래스
                   ┌──────────┬──────────┐
                   │   악성   │   정상   │
┌──────────────────┼──────────┼──────────┤
│ 예측    BLOCK    │   A      │    B     │
│         WARNING  │   C      │    D     │
│         SAFE     │   E      │    F     │
│         DEAD     │   G      │    H     │
└──────────────────┴──────────┴──────────┘
```

| 셀 | 의미 | 평가 |
|----|------|------|
| A | 악성 → BLOCK | ✅ 완벽한 탐지 |
| B | 정상 → BLOCK | ❌ 심각한 오탐 |
| C | 악성 → WARNING | ⚠️ 부분 탐지 |
| D | 정상 → WARNING | 경미한 오탐 |
| E | 악성 → SAFE | ❌ **미탐 (가장 위험)** |
| F | 정상 → SAFE | ✅ 정확한 판정 |
| G,H | DEAD | 평가 제외 |

---

## ⚙️ 현재 점수 설정 (조정 완료)

```python
# react-ai/app/config.py
BLOCK_THRESHOLD = 60
WARNING_THRESHOLD = 35  # 30 → 35 ✅

MISMATCH_SCORE = 15     # 30 → 15 ✅
TYPOSQUATTING_SCORE = 50
NEW_DOMAIN_SCORE = 15
SUSPICIOUS_TLD_SCORE = 10
AI_SCORE_MULTIPLIER = 30
```

---

## 🧪 테스트 실행

```powershell
cd search-ai
uv run python assess_model.py --malicious 100 --benign 100
```

### 예상 출력
```
📊 4×2 혼동 행렬
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          악성    정상
BLOCK      72       2
WARNING    18       8
SAFE        5      85
DEAD        5       5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Block Precision: 97.3%
Detection Rate: 90.0%
Miss Rate: 5.0%
```
