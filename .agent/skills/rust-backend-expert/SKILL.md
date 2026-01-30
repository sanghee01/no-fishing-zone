---
name: rust-backend-expert
description: Vespera, Vespertide, PostgreSQL 기반의 고성능 Rust 백엔드 개발 및 API 설계 지침
---

# Rust Backend Expert Skill (Vespera + Vespertide Stack)

이 스킬은 `aegis-link` 프로젝트의 핵심 백엔드 스택인 Rust, Axum, Vespera, Vespertide, PostgreSQL을 효율적으로 다루기 위한 전문 지침입니다.

## 🦀 주요 원칙

1. **Strong Type Safety**: `Vespertide`로 정의된 스키마와 `Vespera`의 타입 시스템을 결합하여, DB부터 API 응답까지 강력한 타입 안정성을 유지한다.
2. **Zero-Config Discovery**: `Vespera`의 매크로 기반 라우트 시스템을 적극 활용하여 수동 등록 실수를 방지한다.
3. **Explicit Error Handling**: `anyhow` 보다는 도메인 특화 에러 타입을 정의하고, API 응답 시 `Vespera`가 인식할 수 있는 형태로 에러를 반환한다.

## 📋 가이드라인

### 🚀 API 개발 (Vespera + Axum)

- **라우트 핸들러**: 모든 핸들러는 반드시 `pub async fn`으로 작성하며, `src/routes/` 폴더 구조가 곧 API 엔드포인트가 됨을 인지한다.
- **스키마 정의**: 모든 요청/응답 DTO는 `#[derive(vespera::Schema)]`를 적용하여 OpenAPI 문서가 자동 생성되게 한다.
- **필터링**: 모델 객체를 직접 반환하지 말고 `schema_type!` 매크로를 사용하여 필요한 필드만 노출하는 전용 Response 타입을 생성한다.

### 🗄 데이터베이스 (Vespertide + PostgreSQL)

- **스키마 관리**: DB 변경이 필요할 때 직접 SQL을 작성하지 않고, `models/*.json`을 수정한 뒤 `vespertide diff`를 통해 마이그레이션을 생성한다.
- **포스트그레 지원**: PostgreSQL 특화 기능(JSONB, UUID, Timestamptz 등)을 사용할 때 `Vespertide`가 지원하는 표준 타입을 우선 고려하며, 호환성을 체크한다.
- **쿼리 질의**: `Vespertide`가 내보낸(Exported) SeaORM 엔티티 또는 SQL을 활용하여 일관된 쿼리 패턴을 유지한다.

### 🧪 테스트 및 성능

- **Integration**: `cargo test` 실행 전 `docker-compose`로 DB가 준비되었는지 확인하며, 테스트 DB 클린업 로직을 철저히 한다.
- **Performance**: PostgreSQL의 인덱스를 활용할 수 있도록 `Vespertide` 모델 정의 시 `index: true` 설정을 적극 검토한다.

## 🔍 체크리스트

- [ ] 핸들러 함수가 `pub async`인가?
- [ ] DTO 구조체가 `vespera::Schema`를 파생(Derive)하고 있는가?
- [ ] DB 변경 시 `vespertide revision` 과정을 거쳤는가?
- [ ] 에러 발생 시 사용자에게 노출될 메시지와 내부 로그가 분리되었는가?
