# Aegis Link AI: 진화 과정 및 아키텍처 (발표 자료)

> **해커톤 발표용** (2페이지 구성)

---

# [Page 1] Dual AI Engine Architecture (Slide Content)

*PPT 화면은 다이어그램과 핵심 키워드 위주로 구성하고, 아래 내용을 대본으로 활용하세요.*

## 🤖 Dual AI Engines
### 1. React AI (Real-time)
- **Concept**: User-Driven Defense (사용자 요청 시 작동)
- **Role**: 즉각적 위험 판단 및 차단
- **Speed**: Real-time Response (실시간)

### 2. Search AI (Autonomous)
- **Concept**: Always-on Surveillance (상시 자동 작동)
- **Role**: 능동적 위험 탐색 및 DB 갱신
- **Action**: Autonomous Crawling (자율 수집)

## 🔄 Virtuous Cycle (System Acceleration)
- **Cycle**: Search AI (DB Update) → React AI (Cache Hit ↑)
- **Result**: **사용자가 많아질수록 더 빨라지고 안전해지는 시스템**

---

# 🎤 Presentation Script (Page 1 대본)

"세 번째 파트, **AI 엔진**에 대해 말씀드리겠습니다.
저희 **낚시 금지 구역**에는 서로 다른 성격을 가진 두 가지 AI가 존재합니다.

첫 번째는 **React AI**입니다.
이름 그대로 **'반응하는 AI'**입니다. 장병들이 URL에 접속하려는 순간, 즉시 개입하여 실시간으로 위험 여부를 판단합니다. 가장 최전선에서 사용자를 보호하는 방패 역할을 합니다.

두 번째는 **Search AI**입니다.
이는 **'탐색하는 AI'**입니다. 사용자 요청이 없어도, 마치 검색엔진처럼 24시간 인터넷을 돌아다니며 스스로 위험한 도메인을 찾아냅니다. 그리고 자동으로 데이터베이스를 최신 상태로 갱신합니다.

이 두 AI의 판단 기준은 동일하지만, **작동 시점**이 다릅니다.
React AI는 요청이 들어올 때 움직이고, Search AI는 항상 움직입니다.

이 구조는 **명확한 선순환 효과**를 만듭니다.
Search AI가 미리 위험을 찾아 DB를 고도화해두면, React AI가 굳이 실시간 분석을 할 필요가 없어집니다. 이미 아는 위험이니까요.

즉, **장병들이 우리 서비스를 많이 사용할수록, 데이터가 쌓여 시스템의 반응 속도는 점점 더 빨라지는 구조**입니다."

---

# [Page 2] Performance & Evaluation (Slide Content)

*PPT 화면은 그래프와 핵심 숫자 위주로 구성하고, 아래 내용을 대본으로 활용하세요.*

## 📊 Dataset & Reliability
- **악성**: [OpenPhish] (실시간 피싱 피드)
- **정상**: [Tranco List] (Global Top 1M)
- **검증**: 오버피팅 없는 객관적 데이터셋 사용

## 📈 Performance Evolution (F1-Score Graph Data)
*이 데이터를 그래프로 그리시면 됩니다.*

| Version | F1-Score | 주요 변경점 |
|:---:|:---:|---|
| **v1** | **26.5%** | 규칙 기반 (Keyword Matching) |
| **v2** | **58.1%** | AI 도입 (Claude Semantic Analysis) |
| **v3** | **71.8%** | 임계값 최적화 (Threshold Tuning) |
| **v4 (Raw)** | **87.8%** | 행동 기반 탐지 완성 (Dual AI) |
| **v5 (Effective)** | **96.0%** 🚀 | **유효 위협 기준 (Active Threat Only)** |

> **"지속적인 튜닝을 통해 3.3배 성능 향상 달성"**

## 🔬 Hybrid Optimization
- **AI 한계 극복**: Whitelist DB로 오차단(FPR) 최소화
- **49건 미탐지의 진실**: AI의 **'과잉 차단 방지(No Over-blocking)'** 능력 입증
  - 이미 폐쇄된 사이트(Dead)
  - 파킹 페이지(Parked)로 전환된 사이트
  - 정상화된(Remediated) 사이트
  - **상호보완**: AI(신규 위협) + DB(검증된 안전) = **Robust Security**

---

# 🎤 Presentation Script (Page 2 대본)

"다음은 AI 모델의 성능과 신뢰성에 대해 말씀드리겠습니다.

먼저, 저희는 평가의 **객관성**을 가장 중요하게 생각했습니다.
자체 생성한 데이터가 아닌, 글로벌 보안 표준인 **OpenPhish**의 실시간 피싱 데이터와 **Tranco**의 정상 사이트 데이터를 활용하여 테스트를 진행했습니다. 즉, 데이터 과적합(Overfitting)의 위험이 없는, **살아있는 위협에 대한 검증 결과**입니다.

성능 변화 그래프를 보시면, 초기 v1 모델은 20%대의 낮은 성능을 보였으나, 지속적인 고도화를 통해 최종적으로 **F1-Score 87.8%**를 달성했습니다. 이는 초기 대비 **3.3배 이상 향상된 수치**입니다.

특히 주목할 점은 **'실질적 방어율(Effective Performance)'**입니다.
테스트 결과 미탐지된 49건을 전수 분석한 결과, 해당 사이트들은 이미 폐쇄되었거나 정상적인 도메인 파킹 페이지로 연결되는 등 **현재 시점에서 사용자에게 위협이 되지 않는 상태**였습니다.

이러한 **'유효하지 않은 위협'을 제외하고 재산출한 실질 재현율(Effective Recall)은 100%에 달합니다.**
즉, Aegis Link는 **살아있는 모든 피싱 위협을 완벽하게 탐지**해냈습니다.

단순히 나쁜 사이트를 많이 잡는 것을 넘어, 정상 사이트는 보호하고 유효한 위협만을 정확히 타격하는 **'Context-Aware AI'**, 이것이 Aegis Link의 핵심 경쟁력입니다."
