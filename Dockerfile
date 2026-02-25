# PuppyTalk API - Docker 이미지 (추후 Docker 배포용)
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN pip install --no-cache-dir poetry==$POETRY_VERSION
ENV POETRY_VIRTUALENVS_CREATE=false

# 의존성만 먼저 설치 → app/main 변경 시 이 레이어 캐시 재사용
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --no-dev --no-interaction

# 애플리케이션 코드
COPY app/ ./app/
COPY main.py ./

RUN mkdir -p /app/upload

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
