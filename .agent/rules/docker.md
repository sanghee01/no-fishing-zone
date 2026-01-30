---
trigger: model_decision
description: docker-compose.yml, Dockerfile, .dockerignore, nginx.conf 등 인프라 설정 파일을 건드릴 때만 로드됩니다.
---

# Docker & Infrastructure Rules

이 규칙은 `aegis-link` 프로젝트의 인프라 정체성을 유지하고 배포 안정성을 확보하기 위해 에이전트가 항상 준수해야 할 지침입니다.

## ⛔ 절대 금지 사항 (Anti-Patterns)

1. **Secrets Leak**: 어떤 경우에도 `.env` 파일이나 민감한 API 키를 도커 이미지 내부에 `COPY`하거나 버전 관리 시스템(Git)에 포함하지 않는다.
2. **Hardcoded Ports**: 서비스 간 통신 시 `localhost`를 사용하지 않는다. 대신 도커 네트워크 내부의 서비스 이름(예: `http://api:8000`)을 사용한다.
3. **Dirty Images**: `.dockerignore`를 무시하여 `node_modules`, `target`, `.git` 등의 폴더가 이미지 빌드 컨텍스트에 포함되게 하지 않는다.
4. **Manual Runs**: `docker run` 명령어로 개별 컨테이너를 실행하기보다, 항상 `docker compose`를 통해 선언적으로 관리한다.

## ✅ 필수 준수 사항 (Best Practices)

1. **Health Check Awareness**: 새로운 서비스를 추가하거나 수정할 때, 반드시 `healthcheck` 로직이 상호 의존 관계(`depends_on`)와 일치하는지 검계한다.
2. **Nginx Routing Consistency**: 백엔드나 AI 서버의 엔드포인트 구조를 변경하면, Nginx 설정(`default.conf.template`)의 `location` 블록도 함께 업데이트해야 함을 사용자에게 알린다.
3. **Service-Based Logging**: 로그 확인 시 `docker-compose logs -f [service_name]` 방식을 우선적으로 제안한다. (컨테이너 ID 지양)
4. **Multi-stage Build**: 모든 `Dockerfile`은 빌드 속도와 결과물 용량 최적화를 위해 Multi-stage 빌드 구조(builder -> runtime)를 유지한다.
5. **Environment Validation**: 배포 관련 작업 수행 전, `.env.example`과 실제 `.env`의 키값이 일치하는지 습관적으로 점검한다.
