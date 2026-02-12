# PuppyTalk API - Docker 이미지 (추후 Docker 배포용)
FROM python:3.11-slim

# 작업 디렉터리
WORKDIR /app

# 시스템 의존성 (MySQL 클라이언트 등 필요 시 추가)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 복사 후 설치 (캐시 활용)
COPY pyproject.toml ./
COPY app/ ./app/

RUN pip install --no-cache-dir .

# main.py 등 루트 파일 복사
COPY main.py ./

# 업로드 디렉터리 (로컬 스토리지 사용 시)
RUN mkdir -p /app/upload

# 환경 변수는 런타임에 주입 (.env 파일은 이미지에 포함하지 않음)
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# 프로덕션: Gunicorn + Uvicorn worker (워커 수·바인딩은 환경에 맞게 조정)
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
