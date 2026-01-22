FROM python:3.11

# 컨테이너 작업 디렉토리
WORKDIR /app

# 필수 + 개발 편의 시스템 패키지
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    wget \
    git \
    vim \
    nano \
    unzip \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    procps \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# python 기본 설정
# 파일 깔끔
ENV PYTHONDONTWRITEBYTECODE=1
# 로그 즉시 출력
ENV PYTHONUNBUFFERED=1