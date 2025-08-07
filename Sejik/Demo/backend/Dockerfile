# ==============================================================================
# 1단계: 기본 이미지 - 시스템 의존성만 설치
# ==============================================================================
FROM python:3.11-slim as base

# 메타데이터 설정
LABEL maintainer="IBM DoctorAI Team"
LABEL description="Dr.Watson Backend API Server"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 기본 도구 설치 (메모리 절약을 위해 최소한으로)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ==============================================================================
# 2단계: 의존성 빌더 - 컴파일이 필요한 패키지들 설치
# ==============================================================================
FROM base as builder

# 컴파일 도구 설치 (임시로만 사용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip

# 기본 요구사항 먼저 설치 (캐시 활용을 위해)
COPY requirements.txt .

# 의존성을 단계별로 설치하여 메모리 압박 감소
RUN pip install --no-cache-dir --user \
    fastapi==0.116.1 \
    uvicorn==0.35.0 \
    pydantic==2.11.7 \
    SQLAlchemy==2.0.42 \
    pymysql==1.1.1

# 나머지 패키지들 설치
RUN pip install --no-cache-dir --user \
    aiosmtplib==3.0.2 \
    fastapi-mail==1.5.0 \
    fastapi-sso==0.18.0 \
    cryptography==43.0.1

# Google API 관련 패키지들
RUN pip install --no-cache-dir --user \
    google-auth==2.25.2 \
    google-auth-oauthlib==1.1.0 \
    google-api-python-client==2.148.0

# IBM Watson 패키지 (가장 큰 패키지를 마지막에)
RUN pip install --no-cache-dir --user \
    ibm-watson-machine-learning==1.0.368 \
    ibm-watson==8.1.0

# 나머지 작은 패키지들
RUN pip install --no-cache-dir --user \
    python-dotenv==1.1.1 \
    python-multipart==0.0.18 \
    PyJWT==2.10.1 \
    PyYAML==6.0.2 \
    pytz==2023.3 \
    python-dateutil==2.9.0 \
    pydub==0.25.1 \
    python-magic==0.4.27

# ==============================================================================
# 3단계: OCR 의존성 설치
# ==============================================================================
FROM base as ocr-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# OCR 관련 Python 패키지
RUN pip install --no-cache-dir --user \
    pytesseract==0.3.13 \
    Pillow==10.4.0 \
    PyPDF2==3.0.1

# ==============================================================================
# 4단계: 미디어 처리 의존성
# ==============================================================================
FROM base as media-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ==============================================================================
# 5단계: 최종 런타임 이미지
# ==============================================================================
FROM base as final

# 필요한 런타임 라이브러리만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    ffmpeg \
    libmagic1 \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# 빌더 스테이지에서 설치된 Python 패키지들 복사
COPY --from=builder /root/.local /root/.local
COPY --from=ocr-deps /root/.local /root/.local

# PATH에 사용자 패키지 경로 추가
ENV PATH=/root/.local/bin:$PATH

# 비root 사용자 생성
RUN useradd --create-home --shell /bin/bash app

# 애플리케이션 코드 복사
COPY --chown=app:app . .

# 권한 설정
RUN chown -R app:app /app

# 사용자 전환
USER app

# 포트 8000 노출
EXPOSE 8000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]