---
name: docker-master
description: Docker 및 docker-compose를 활용한 프로젝트 환경 관리 및 도커라이징 지침
---

# Docker Master Skill (Aegis-Link Context)

이 스킬은 `aegis-link` 프로젝트의 다중 서비스 환경(Rust, Next.js, Python, PostgreSQL)을 Docker로 관리하고 배포하기 위한 전문 가이드입니다.

## � 핵심 개념 비유 (이해를 돕기 위한 기준)

1. **이미지 (Image)**: 프로그램을 실행하기 위한 모든 것이 담긴 **'설치 CD'** 또는 **'건축 설계도'**. 한 번 만들어지면 변하지 않으며, 환경 변수는 이미지 밖에 두어야 한다.
2. **컨테이너 (Container)**: 이미지를 실행시킨 **'실제 상태'**. 설계도대로 지은 **'실제 건물'**이며, 하나의 이미지로 여러 컨테이너를 띄울 수 있다.
3. **Dockerfile**: 이미지를 만들기 위한 **'조립 설명서'**. 텍스트 파일이므로 Git으로 관리 가능하다.
4. **Docker Compose**: 여러 서비스를 한꺼번에 관리하는 **'종합 지휘 본부'**.

## 🏗 프로젝트 구조 및 네트워크

`aegis-link`는 다음과 같은 리버스 프록시 구조를 가진다:

- **Nginx (Port 80)**: 모든 요청의 입구 (리버스 프록시).
  - `/` -> 프론트엔드 (Node/Next.js:3000)
  - `/api/` -> 백엔드 (Rust/Vespera:8000)
  - `/ai/` -> AI 서버 (Python:8001)
- **PostgreSQL (Port 5432)**: 데이터베이스. `api` 컨테이너가 SQL 질의를 보낸다.

## 🛠 주요 명령어 가이드 (Habits)

제가 작업을 수행할 때 다음 명령어 패턴을 우선적으로 사용합니다:

- **서비스 실행**: `docker compose up api postgres` (필요한 서비스만 골라 켜기)
- **로그 확인**: `docker compose logs -f api` (특정 팀원의 보고서 읽기)
- **상태 체크**: `docker compose ps` (현장 출석 체크)
- **완전 삭제**: `docker compose down -v` (철거 및 장비 정리)

## 🐳 Dockerfile 작성 원칙 (Multi-stage Build)

최종 결과물을 가볍게 만들기 위해 다음 구조를 유지한다:

1. **빌드 단계 (`AS builder`)**: `rustlang/rust:nightly` 등 무거운 환경에서 소스 코드를 컴파일하고 실행 파일을 생성.
2. **실행 단계 (`FROM debian:bookworm-slim`)**: 빌드 도구는 빼고, 실행 파일만 복사하여 아주 가벼운 컨테이너 생성.
3. **환경 격리**: 각 서비스(`backend`, `frontend`, `ai`)는 저마다의 `Dockerfile`을 가지며 환경을 섞지 않는다.

## ⚠️ 관리 포인트

- **.env 관리**: 비밀번호 등 민감한 정보는 절대 이미지에 넣지 않고, 서버의 `.env` 파일을 통해 주입한다.
- **.dockerignore**: `target/`, `.git/`, `.env` 등을 빌드 컨텍스트에서 제외하여 빌드 속도를 높이고 보안을 유지한다.
- **Health Check**: 컨테이너가 단순히 켜져 있는 것을 넘어, 실제로 요청을 처리할 수 있는지 `/health` 엔드포인트를 통해 5초마다 확인한다.

## � 체크리스트

- [ ] 신규 서비스 추가 시 `docker-compose.yml`의 `services`에 등록했는가?
- [ ] Nginx 설정 파일에 새로운 엔드포인트 라우팅을 반영했는가?
- [ ] `.dockerignore`에 로컬 빌드 결과물(`target/`, `node_modules/`)이 포함되어 있는가?
- [ ] 환경 변수가 하드코딩되지 않고 `.env`를 통해 주입되는가?
