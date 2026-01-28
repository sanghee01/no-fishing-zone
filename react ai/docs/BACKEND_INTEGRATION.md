# 🛡️ Python AI 분석 서버 - 프로젝트 구조 및 백엔드 연동 가이드

## 📁 프로젝트 파일 구조

```
python/
├── 📄 pyproject.toml        # uv 패키지 관리 설정 (의존성 목록)
├── 📄 uv.lock               # 의존성 버전 잠금 파일
├── 📄 .env.example          # 환경 변수 템플릿
├── 📄 .env                  # 실제 API 키 설정 (gitignore 대상)
├── 📄 README.md             # 프로젝트 소개 및 실행 방법
│
├── 📂 app/                  # 메인 애플리케이션 폴더
│   ├── 📄 __init__.py       # 패키지 초기화 파일
│   ├── 📄 main.py           # FastAPI 서버 진입점 (엔드포인트 정의)
│   ├── 📄 config.py         # 환경 설정 및 상수 정의
│   ├── 📄 models.py         # 요청/응답 데이터 스키마 (Pydantic)
│   │
│   ├── 📂 services/         # 핵심 비즈니스 로직
│   │   ├── 📄 __init__.py
│   │   ├── 📄 analyzer.py       # 🎯 메인 파이프라인 오케스트레이터
│   │   ├── 📄 whitelist.py      # Phase 0: 화이트리스트 검사
│   │   ├── 📄 redirect.py       # Phase 1: 리다이렉트 추적
│   │   ├── 📄 metadata.py       # Phase 2: 도메인 메타데이터
│   │   ├── 📄 ai_analyzer.py    # Phase 3: Claude AI 분석
│   │   └── 📄 search_verifier.py # Phase 4: 검색 엔진 검증
│   │
│   └── 📂 utils/            # 유틸리티 함수
│       ├── 📄 __init__.py
│       ├── 📄 preprocessor.py   # HTML 전처리 (토큰 절약)
│       └── 📄 domain.py         # 도메인 추출 유틸리티
│
└── 📂 data/                 # 정적 데이터
    └── 📄 whitelist.txt     # 신뢰 도메인 목록 (270개+)
```

---

## 🔗 Rust 백엔드 연동 방법

### 1. API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 헬스체크 (서버 상태 확인) |
| GET | `/health` | 상세 헬스체크 |
| POST | `/analyze` | **URL 분석 요청 (메인 기능)** |

---

### 2. 요청/응답 규격

#### 📤 요청 (Rust → Python)

```json
POST /analyze
Content-Type: application/json

{
  "url": "https://suspicious-site.xyz",
  "request_id": "req_20260128_001"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `url` | string | 분석할 URL (필수) |
| `request_id` | string | 추적용 요청 ID (필수) |

---

#### 📥 응답 (Python → Rust)

```json
{
  "url": "https://suspicious-site.xyz",
  "status": "WARNING",
  "risk_score": 45,
  "category": "Common",
  "keyword": "신한은행",
  "reasons": [
    "New domain (3 days old) (+15)",
    "Suspicious TLD: .xyz (+10)",
    "AI risk assessment: 0.35 (+10)",
    "Domain mismatch: not in search results (+30)"
  ]
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `url` | string | 분석된 URL |
| `status` | enum | `SAFE` / `WARNING` / `BLOCK` |
| `risk_score` | int | 총 위험 점수 (0~100+) |
| `category` | string | `Common` (일반) / `Negative` (불법) / `Trusted` (화이트리스트) |
| `keyword` | string | AI가 감지한 브랜드명 |
| `reasons` | array | 각 Phase에서 발생한 점수 근거 |

---

### 3. Rust에서 호출하는 예시

```rust
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct AnalyzeRequest {
    url: String,
    request_id: String,
}

#[derive(Deserialize)]
struct AnalyzeResponse {
    url: String,
    status: String,        // "SAFE" | "WARNING" | "BLOCK"
    risk_score: i32,
    category: String,
    keyword: String,
    reasons: Vec<String>,
}

async fn analyze_url(url: &str, request_id: &str) -> Result<AnalyzeResponse, reqwest::Error> {
    let client = Client::new();
    
    let response = client
        .post("http://localhost:8000/analyze")  // Python 서버 주소
        .json(&AnalyzeRequest {
            url: url.to_string(),
            request_id: request_id.to_string(),
        })
        .send()
        .await?
        .json::<AnalyzeResponse>()
        .await?;
    
    Ok(response)
}
```

---

### 4. 상태(Status) 처리 로직

```rust
match response.status.as_str() {
    "SAFE" => {
        // 정상 사이트 - 접속 허용
        allow_access();
    }
    "WARNING" => {
        // 의심 사이트 - 경고 표시 후 사용자 선택
        show_warning_dialog(&response.reasons);
    }
    "BLOCK" => {
        // 위험 사이트 - 접속 차단
        block_access(&response.keyword);
    }
}
```

---

### 5. 점수 기준표

| 점수 범위 | 상태 | 권장 동작 |
|-----------|------|-----------|
| 0~29 | SAFE | 접속 허용 |
| 30~59 | WARNING | 경고 표시 |
| 60+ | BLOCK | 접속 차단 |

---

## 🚀 Python 서버 실행

```powershell
cd c:\Users\mnb09\Desktop\aegis-link\python
uv sync                                    # 의존성 설치
uv run uvicorn app.main:app --port 8000    # 서버 실행
```

**Swagger UI**: http://localhost:8000/docs

---

## ⚠️ 주의사항

1. **`.env` 파일 필수**: `ANTHROPIC_API_KEY` 설정 필요
2. **네트워크 접근**: Python 서버가 외부 API(Anthropic, Google, Naver)에 접근 가능해야 함
3. **타임아웃**: 기본 요청 타임아웃 10초 (config.py에서 설정)
4. **동시성**: FastAPI가 비동기 처리하므로 다수 요청 동시 처리 가능
