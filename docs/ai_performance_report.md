# 🎯 React-AI 성능 테스트 보고서

> **테스트 일시**: 2026-02-07 03:30 KST  
> **테스트 환경**: Docker Container (search-ai)  
> **데이터셋**: OpenPhish (악성 300개 중 50개 샘플) + Tranco (정상 1M 중 50개 샘플)

---

## 📊 테스트 결과 요약

### 4×2 혼동 행렬

```
┌──────────────────────────────────────────────────┐
│                 실제 클래스                        │
│              악성         정상                    │
├──────────────────────────────────────────────────┤
│ 예측  BLOCK      8          8                    │
│       WARNING   24          6                    │
│       SAFE      18         36                    │
│       FAIL       0          0                    │
└──────────────────────────────────────────────────┘
```

### 📈 성능 지표

| 지표 | 값 | 목표 | 평가 |
|------|-----|------|------|
| **Detection Rate** (탐지율) | 64.0% | 90%+ | ⚠️ 개선 필요 |
| **Miss Rate** (미탐율) | 36.0% | 5% 미만 | ❌ 높음 |
| **Block Precision** (차단 정밀도) | 50.0% | 95%+ | ❌ 낮음 |
| **False Block Rate** (오차단율) | 16.0% | 3% 미만 | ❌ 개선 필요 |

---

## 🔍 분석

### 악성 URL 분류 결과 (50개)
- **BLOCK**: 8개 (16%) - 즉시 차단
- **WARNING**: 24개 (48%) - 주의 표시
- **SAFE**: 18개 (36%) - 미탐지 ❌
- **FAIL**: 0개 - 접속 오류 없음

### 정상 URL 분류 결과 (50개)
- **BLOCK**: 8개 (16%) - 오차단 ❌
- **WARNING**: 6개 (12%) - 경미한 오탐
- **SAFE**: 36개 (72%) - 정상 판정 ✅
- **FAIL**: 0개

---

## 📋 데이터셋 정보

### OpenPhish (악성 URL)
- **출처**: https://openphish.com/
- **갱신 주기**: 12시간
- **특징**: 실시간 피싱 URL, Dead URL 비율 낮음
- **자동 업데이트**: Docker 시작 시 자동 다운로드

### Tranco (정상 URL)
- **출처**: Tranco Top 1M 랭킹
- **특징**: 글로벌 상위 도메인, 안정적인 화이트리스트

---

## ⚙️ 현재 점수 임계값

```python
# react-ai/app/config.py
BLOCK_THRESHOLD = 55      # 55점 이상 → BLOCK
WARNING_THRESHOLD = 35    # 35점 이상 → WARNING
SAFE_THRESHOLD = 35       # 35점 미만 → SAFE

MISMATCH_SCORE = 15       # 검색엔진 미매칭 페널티
AI_SCORE_MULTIPLIER = 30  # Claude AI 분석 가중치
```

---

## 🚀 개선 방향

### 1. 탐지율 향상 (현재 64% → 목표 90%)
- Claude AI 분석 가중치 조정 (`AI_SCORE_MULTIPLIER`)
- 피싱 특징 패턴 추가 탐지

### 2. 오차단율 감소 (현재 16% → 목표 3%)
- `BLOCK_THRESHOLD` 상향 조정 검토
- 화이트리스트 확장

### 3. 미탐율 감소 (현재 36% → 목표 5%)
- 검색 엔진 미매칭 점수 조정
- 새 도메인 페널티 추가

---

## 📝 테스트 명령어

```bash
# Docker 내부에서 실행
docker compose exec search-ai uv run python assess_model.py --limit 100

# 전체 테스트 (시간 소요)
docker compose exec search-ai uv run python assess_model.py --limit 300
```

---

## 📁 관련 파일

| 파일 | 설명 |
|------|------|
| `assess_model.py` | 성능 평가 스크립트 |
| `seeds/openphish.txt` | OpenPhish 악성 URL 목록 |
| `seeds/1000000white.csv` | Tranco 화이트리스트 |
| `react-ai/app/config.py` | 점수 임계값 설정 |

---

*이 보고서는 자동 생성되었습니다.*
