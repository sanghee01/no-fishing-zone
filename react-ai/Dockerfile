FROM python:3.13-slim

WORKDIR /app

# 시스템 의존성 설치 (필요한 경우). 기본적으로는 불필요하지만 일부 파이썬 라이브러리(gcc 등)를 위해 필요할 수 있음.
# RUN apt-get update && apt-get install -y gcc

# 프로젝트 정의 파일 복사
COPY pyproject.toml .

# 의존성 설치
# pyproject.toml에서 직접 설치하기 위해 pip 사용
RUN pip install --no-cache-dir .

# 나머지 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8001

# 애플리케이션 실행
# 'app/main.py' 내의 'app' 객체 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
