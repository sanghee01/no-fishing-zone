---
trigger: model_decision
description: backend/ 폴더 내의 코드나, DB 모델(models/*.json), 마이그레이션 파일들을 수정할 때만 로드됩니다.
---

# VESPERTIDE KNOWLEDGE BASE (Rules)

## ColumnType Usage (CRITICAL)

```rust
// CORRECT - Always use wrapped variant
ColumnType::Simple(SimpleColumnType::Integer)
SimpleColumnType::Integer.into()

// WRONG - Old flat syntax
ColumnType::Integer  // Does not exist
```

## ColumnDef Initialization

ALL fields required including inline constraint fields:

```rust
ColumnDef {
    name, r#type, nullable, default, comment,
    primary_key: None,   // Must include
    unique: None,        // Must include
    index: None,         // Must include
    foreign_key: None,   // Must include
}
```

## Naming Conventions

- Indexes: `ix_{table}__{columns}` or `ix_{table}__{name}`
- Unique: `uq_{table}__{columns}`
- Foreign keys: `fk_{table}__{columns}`

## Anti-Patterns

- `ColumnType::Integer` 대신 `ColumnType::Simple(SimpleColumnType::Integer)` 사용 필수.
- `ColumnDef` 생성 시 4가지 Option 필드(`primary_key`, `unique`, `index`, `foreign_key`) 누락 금지.
- 마이그레이션 시 Raw SQL 지양, `MigrationAction` enum 사용.
- `TableDef`에 대해 `normalize()` 호출 필수 (인라인 제약 조건 변환용).

## Database Backends

- PostgreSQL: Full support (`"identifier"`)
- MySQL: Full support (`` `identifier` ``)
- SQLite: Limited ALTER support (Temp table workarounds 사용)
