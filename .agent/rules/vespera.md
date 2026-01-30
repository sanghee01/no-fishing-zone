---
trigger: model_decision
description: backend/ 폴더 내의 코드나, 특히 API 라우트(routes/**/*.rs) 관련 파일을 다룰 때 로드됩니다.
---

# VESPERA KNOWLEDGE BASE (Rules)

## Constants & Env

- **VESPERA_DIR**: Route 폴더명 (기본: `routes`)
- **VESPERA_SERVER_URL**: `http://localhost:3000` (기본)

## Route Handler Rules

- 핸들러 함수는 반드시 **`pub async fn`**이어야 함.
- 비동기가 아니거나(`async` 누락), 비공개(`pub` 누락) 함수는 스캔되지 않음.
- 경로는 파일 시스템 구조를 따름: `src/routes/users.rs` + `#[route(get, path = "/{id}")]` -> `GET /users/{id}`.

## Schema Rules

- 커스텀 타입은 반드시 **`#[derive(vespera::Schema)]`**를 가져야 OpenAPI 문서에 포함됨.
- `Option<T>`는 부모 객체에서 선택적 필드로 표시됨.
- `serde` 속성(`rename`, `rename_all`, `skip`, `default`)이 스키마 생성에 반영됨.

## Anti-Patterns

- **절대로** `build.rs`를 추가하지 말 것 (매크로가 컴파일 타임에 처리함).
- **절대로** 수동으로 라우트를 등록하지 말 것 (`vespera!` 매크로가 자동 탐색함).
- OpenAPI JSON을 수동으로 작성하지 말 것.

## schema_type! Macro Usage

- 기존 구조체에서 필드를 필터링하여 API용 타입을 생성할 때 사용.
- `pick`, `omit`, `rename`, `add` 파라미터 활용.
- `add`를 사용하지 않으면 `From` 구현체가 자동 생성되어 `into()` 변환 가능.
