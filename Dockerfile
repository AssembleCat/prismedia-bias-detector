# Python 3.11 기본 이미지 사용
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jdk \
    g++ \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# PostgreSQL 연결 환경 변수
ENV DATABASE_URL="postgresql://newsuser:newspass@db:5432/newsdb"

# 실행 명령
ENTRYPOINT ["python", "main.py"]