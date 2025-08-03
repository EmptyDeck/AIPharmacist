# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 메타데이터 설정
LABEL maintainer="IBM DoctorAI Team"
LABEL description="Dr.Watson Backend API Server"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (OCR을 위한 Tesseract 포함)
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 8000 노출
EXPOSE 8000

# 비root 사용자 생성 및 권한 설정
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]