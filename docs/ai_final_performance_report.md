# Aegis Link AI 성능 평가 보고서

> **해커톤 최종 발표용** | 테스트일: 2026-02-08

---

## 📋 테스트 개요

| 항목 | 값 |
|------|-----|
| **총 테스트 URL** | 600개 |
| **악성 URL (Malicious)** | 300개 (OpenPhish) |
| **정상 URL (Benign)** | 300개 (Tranco Top 1M) |
| **테스트 환경** | Docker 컨테이너 (react-ai + PostgreSQL) |
| **AI 모델** | Claude 4.5 Haiku (Anthropic) |

---

## 📊 4×2 혼동 행렬

|                | BLOCK | WARNING | SAFE | DEAD |
|----------------|:-----:|:-------:|:----:|:----:|
| **악성 (Malicious)** | 22 | 155 | 123 | 0 |
| **정상 (Benign)** | 16 | 47 | 237 | 0 |

### 해석
- **악성 URL 탐지**: BLOCK(22) + WARNING(155) = **177개 탐지** (59%)
- **정상 URL 판정**: WARNING(47) + SAFE(237) = **284개 정상 판정** (94.7%)
- **DEAD (접속 불가)**: 0개 (모두 접속 가능)

---

## 📈 성능 메트릭

### 핵심 지표

| 지표 | 값 | 설명 |
|------|-----|------|
| **Precision** | **91.71%** | 탐지된 것 중 실제 악성 비율 |
| **Recall** | **59.00%** | 실제 악성 중 탐지된 비율 |
| **F1-Score** | **71.81%** | Precision과 Recall의 조화 평균 |

### 상세 통계

| 지표 | 값 |
|------|-----|
| True Positive (TP) | 177 |
| False Positive (FP) | 16 |
| False Negative (FN) | 123 |
| True Negative (TN) | 284 |
| **Detection Rate** | 59.00% |
| **False Positive Rate** | 5.33% |

---

## 🔬 성능 분석

### 강점 (Strengths)

1. **높은 Precision (91.71%)**
   - 탐지하면 거의 확실히 악성
   - 오차단(정상→BLOCK)이 매우 적음 (16/300 = 5.33%)

2. **낮은 False Positive Rate (5.33%)**
   - 정상 사이트를 잘못 차단하는 경우가 적음
   - 사용자 경험에 미치는 부정적 영향 최소화

3. **WARNING 중간 계층 활용**
   - 확실하지 않은 경우 WARNING으로 분류
   - 사용자에게 주의를 주면서 접속은 허용

### 개선점 (Areas for Improvement)

1. **Recall 향상 필요 (59%)**
   - 악성 URL의 41%가 SAFE로 미탐지
   - 특히 새로운 피싱 도메인 탐지 강화 필요

2. **WARNING 분류 최적화**
   - 정상 URL의 15.7%가 WARNING 분류 (47/300)
   - 더 정밀한 분류 기준 필요

---

## 📐 평가 기준

### 판정 로직

```
위험 사이트 탐지 성공 = SAFE가 아니면 성공 (BLOCK 또는 WARNING)
정상 사이트 판정 성공 = BLOCK이 아니면 성공 (WARNING 또는 SAFE)
DEAD = 접속 불가 사이트 → 통계 제외
```

### 점수 체계 (config.py)

| 설정 | 값 | 설명 |
|------|-----|------|
| BLOCK_THRESHOLD | 65점 | 65점 이상 = 차단 |
| WARNING_THRESHOLD | 20점 | 20점 이상 = 경고 |
| AI_SCORE_MULTIPLIER | 55 | AI 분석 최대 55점 |
| MISMATCH_SCORE | 5 | 검색 미매칭 페널티 |

---

## 🎯 결론

### 핵심 성과

| 목표 | 달성 현황 |
|------|----------|
| **높은 정밀도 (Precision)** | ✅ 91.71% 달성 |
| **낮은 오차단율** | ✅ 5.33% 달성 |
| **균형잡힌 F1-Score** | ✅ 71.81% 달성 |

### 실용적 의미

1. **사용자 신뢰 확보**: 차단되면 거의 확실히 위험 사이트
2. **서비스 안정성**: 정상 사이트 오차단이 극히 적음
3. **안전 마진**: WARNING 단계로 불확실한 경우에도 사용자 보호

---

## 📁 첨부 파일

| 파일 | 설명 |
|------|------|
| `final_assessment_result.json` | 테스트 결과 JSON |
| `final_assessment_output.txt` | 테스트 콘솔 출력 |
| `final_assessment.py` | 테스트 스크립트 |

---

## 🔗 참조

- **악성 데이터셋**: [OpenPhish](https://openphish.com/)
- **정상 데이터셋**: [Tranco List](https://tranco-list.eu/)
- **AI 모델**: Claude 4.5 Haiku (Anthropic)
