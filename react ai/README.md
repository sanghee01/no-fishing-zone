# Python AI 분석 서버

Rust 메인 서버로부터 전달받은 Unknown URL에 대해 5단계(Phase 0~4) 심층 분석을 수행하는 FastAPI 기반 Microservice입니다.

## 설치 (uv 사용)

```bash
# uv 설치 (이미 설치되어 있다면 생략)
# https://docs.astral.sh/uv/getting-started/installation/

# 의존성 설치
uv sync
```

## 환경 설정

`.env.example`을 `.env`로 복사하고 API 키를 설정하세요:

```bash
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 설정
```

## 실행

```bash
uv run uvicorn app.main:app --reload --port 8000
```

## API 엔드포인트

### POST /analyze

**Request:**
```json
{
  "url": "https://example.com",
  "request_id": "req_001"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "status": "SAFE | WARNING | BLOCK",
  "risk_score": 0,
  "category": "Common",
  "keyword": "",
  "reasons": []
}
```

## 분석 파이프라인

- **Phase 0**: 화이트리스트 필터링
- **Phase 1**: 리다이렉트 추적 (+5점/회, 20회 초과 시 BLOCK)
- **Phase 2**: 도메인 메타데이터 (신규 +15점, 수상한 TLD +10점)
- **Phase 3**: Claude Haiku 4.5 시맨틱 분석 (최대 +30점)
- **Phase 4**: 검색 엔진 교차 검증 (유사/변조 +50점, 불일치 +30점)
