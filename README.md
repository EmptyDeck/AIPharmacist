# 🏥 IBM DoctorAI - AI-Powered Pharmaceutical Consultation Platform

## 🎥 프로젝트 데모 영상

[![IBM DoctorAI Demo Video](https://img.youtube.com/vi/uNyeoSGKiCs/maxresdefault.jpg)](https://youtu.be/uNyeoSGKiCs)

> 🔗 **[📺 YouTube에서 전체 데모 보기](https://youtu.be/uNyeoSGKiCs)**


<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/React-19.1.1-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-Latest-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/IBM_Watson-AI-052FAD.svg" alt="IBM Watson">
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1.svg" alt="MySQL">
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED.svg" alt="Docker">
</div>

# 프로젝트 개요

IBM DoctorAI는 IBM Watson 기술을 활용한 종합 의료 AI 상담 플랫폼입니다. 다양한 AI 에이전트를 통해 의료 상담, 약물 정보 제공, 일정 관리, 문서 처리 등의 서비스를 제공합니다.

### 주요 특징
- **🤖 다중 AI 에이전트 시스템**: 전문화된 의료 상담 AI들
- **🎤 음성 대화 지원**: 실시간 음성 인식 및 합성
- **📄 의료 문서 처리**: OCR을 통한 처방전 및 문서 분석
- **📅 일정 관리**: Google 캘린더 연동 복약 알림
- **💊 약물 데이터베이스**: 포괄적인 의약품 정보 및 상호작용 검사

## 시스템 아키텍처

![architecture](https://github.com/user-attachments/assets/591fd7fc-4053-47d5-a602-c4328e765a1)


### AI 에이전트 구성
- **ExplainAI**: 약물 정보 전문가 - 의약품 효능, 용법, 성분 설명
- **WarnAI**: 안전 경고 전문가 - 부작용, 금기사항, 약물 상호작용
- **CalendarAI**: 일정 관리 전문가 - 복약 스케줄, 병원 예약 관리
- **GeneralAI**: 일반 상담 - 종합적인 의료 상담 및 조언

## 📁 프로젝트 구조

```
IBM_DoctorAI/
├──  backend/                    # FastAPI 백엔드 서버
│   ├── api/                      # REST API 엔드포인트
│   │   ├── chatbot/             # AI 에이전트들
│   │   │   ├── explainAI.py     # 약물 정보 전문가
│   │   │   ├── warnAI.py        # 안전 경고 전문가
│   │   │   └── calendarAI.py    # 일정 관리 전문가
│   │   ├── chat.py              # 메인 채팅 인터페이스
│   │   ├── voice.py             # 음성 처리
│   │   ├── calendar.py          # 캘린더 연동
│   │   └── file_upload.py       # 파일 업로드 처리
│   ├── DB/database.py           # 데이터베이스 모델
│   ├── utils/                   # 유틸리티 서비스
│   └── main.py                  # 애플리케이션 진입점
├──  frontend/                   # React 프론트엔드
│   ├── src/pages/
│   │   ├── ChatPage/            # 메인 채팅 인터페이스
│   │   ├── LoginPage/           # 로그인 페이지
│   │   ├── MainPage/            # 랜딩 페이지
│   │   └── MailPage/            # 이메일 관리
│   └── src/apis/apis.js         # API 통신
├──  medical_chatbot_package/    # 독립형 ML 패키지
│   ├── medical_model.py         # 핵심 의료 AI 모델
│   ├── utils/watsonx_client.py  # Watson 연동
│   └── data/drug_data.csv       # 의료 데이터베이스
└──  Examples/                   # 개발 예제들
    ├── RAG AI Chatbot/          # RAG 구현 예제
    ├── OCR/                     # 문서 처리 예제
    ├── 음성대화/                  # 음성 상호작용 예제
    └── 캘린더/                    # 캘린더 연동 예제
```

## 빠른 시작

### 📋 필수 요구사항

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **IBM Watson 계정 및 API 키**
- **Google Cloud Console 프로젝트**

### 🔧 설치 및 설정

#### 1️⃣ 레포지토리 클론
```bash
git clone https://github.com/your-org/IBM_DoctorAI.git
cd IBM_DoctorAI
```

#### 2️⃣ 백엔드 설정
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키들을 설정하세요
```

#### 3️⃣ 환경 변수 설정 (.env 파일)
```env
# IBM Watson 설정
WATSONX_API_URL=https://us-south.ml.cloud.ibm.com
WATSONX_API_KEY=your_watson_api_key
WATSONX_PROJECT_ID=your_project_id

# IBM Watson STT/TTS
WATSON_STT_API_KEY=your_stt_api_key
WATSON_STT_URL=your_stt_service_url
WATSON_TTS_API_KEY=your_tts_api_key
WATSON_TTS_URL=your_tts_service_url

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URIS=http://localhost:8001

# 데이터베이스
DATABASE_URL=mysql+pymysql://ibm.doctor-user:ibm.doctor-pass@localhost:3306/ibm.doctor-db

# 이메일 설정 (선택사항)
MAIL_USERNAME=your_email@naver.com
MAIL_PASSWORD=your_app_password
```

#### 4️⃣ 데이터베이스 설정
```bash
# Docker로 MySQL 실행
docker-compose up mysql -d

# 또는 전체 스택 실행
docker-compose up -d
```

#### 5️⃣ 백엔드 서버 실행
```bash
# 개발 모드로 실행
python main.py

# 서버가 http://localhost:8001 에서 실행됩니다
```

#### 6️⃣ 프론트엔드 설정
```bash
cd ../frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm start

# 프론트엔드가 http://localhost:3000 에서 실행됩니다
```

## 🤖 AI 에이전트 시스템

### 전문화된 의료 AI 에이전트들

| 에이전트 | 역할 | 전문 분야 |
|---------|------|----------|
| **ExplainAI** | 약물 정보 전문가 | 의약품 효능, 용법, 성분 설명 |
| **WarnAI** | 안전 경고 전문가 | 부작용, 금기사항, 약물 상호작용 |
| **CalendarAI** | 일정 관리 전문가 | 복약 스케줄, 병원 예약 관리 |
| **GeneralAI** | 일반 상담 | 종합적인 의료 상담 및 조언 |

### AI 모델 상세

```
사용한 AI 모델: "ibm/granite-3-3-8b-instruct"
Provider: IBM WatsonX
Capabilities:
- 의료 전문 지식 기반 대화
- 한국어 네이티브 지원
- 컨텍스트 인식 대화
- 전문 의료 용어 처리
```

## 주요 기능

### 💬 대화형 의료 상담
- **실시간 채팅**: WebSocket 기반 실시간 대화
- **컨텍스트 유지**: 대화 히스토리를 통한 맥락 이해
- **전문 분야별 라우팅**: 질문 유형에 따른 적절한 AI 에이전트 선택

### 🎤 음성 상호작용
```
음성 처리 파이프라인:
Audio Input → Watson STT → Text Processing → AI Response → Watson TTS → Audio Output
```

### 📄 문서 처리 시스템
- **OCR 엔진**: Tesseract 기반 한국어 처방전 인식
- **PDF 처리**: PyPDF2를 통한 의료 문서 텍스트 추출
- **이미지 분석**: Pillow 기반 의료 이미지 전처리

### 📅 일정 관리
- **Google Calendar 연동**: 복약 알림 자동 등록
- **스마트 스케줄링**: AI 기반 최적 복약 시간 제안
- **알림 시스템**: 이메일 및 캘린더 푸시 알림

### 💊 의약품 데이터베이스
```
포함된 의약품 정보:
- 제품명, 주성분, 제조회사
- 효능/효과, 용법/용량
- 사용상 주의사항
- 약물 상호작용
- 부작용 정보
- 금기사항
```

##  API 문서

### 📡 주요 엔드포인트

| 메소드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `POST` | `/api/chat` | 메인 채팅 인터페이스 |
| `POST` | `/api/voice/stt` | 음성-텍스트 변환 |
| `POST` | `/api/voice/tts` | 텍스트-음성 변환 |
| `POST` | `/api/file-upload` | 의료 문서 업로드 |
| `GET` | `/api/calendar/events` | 복약 일정 조회 |
| `POST` | `/api/calendar/create` | 일정 생성 |
| `GET` | `/auth/google/login-enhanced` | Google OAuth 로그인 |

### 📝 API 사용 예제

```python
# 채팅 API 호출 예제
import requests

response = requests.post("http://localhost:8001/api/chat", json={
    "message": "아스피린의 부작용이 궁금해요",
    "user_id": "user123",
    "context": {
        "current_medications": ["혈압약"],
        "allergies": ["페니실린"]
    }
})

print(response.json())
```

## Docker 배포

### 개발 환경
```bash
# 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 프로덕션 배포
```bash
# 프로덕션 빌드
docker-compose -f docker-compose.prod.yml up -d

# SSL 설정 (스크립트 제공)
./setup-ssl.sh
```

## 🔒 보안 및 인증

### 🛡️ 구현된 보안 기능
- **Google OAuth 2.0**: 소셜 로그인 인증
- **JWT 토큰**: 세션 관리 및 API 인증
- **HTTPS/SSL**: 전송 계층 암호화
- **입력 검증**: SQLAlchemy ORM 및 Pydantic 기반
- **Rate Limiting**: API 호출 빈도 제한

### 🔐 개인정보 보호
- **최소 정보 수집**: 필수 의료 정보만 저장
- **암호화 저장**: 민감한 의료 정보 암호화
- **접근 제어**: 사용자별 데이터 격리

## 모니터링 및 로깅

### 📊 구현된 모니터링
```
로깅 시스템:
- 사용자 상호작용 로그
- AI 응답 품질 메트릭
- 시스템 성능 지표
- 오류 및 예외 추적
```

### 📋 헬스 체크
```bash
# 시스템 상태 확인
curl http://localhost:8001/health

# 응답 예시
{
    "status": "healthy",
    "database": "connected",
    "watson_ai": "available",
    "timestamp": "2024-01-15T10:30:00Z"
}

```

### 🔍 테스트 커버리지
- **단위 테스트**: AI 에이전트 개별 기능
- **통합 테스트**: API 엔드포인트 전체 플로우
- **E2E 테스트**: 사용자 시나리오 기반 테스트

## 배포 가이드

### ☁️ 클라우드 배포 (EC2)
```bash
# 배포 스크립트 실행
./deploy-ubuntu.sh

# SSL 인증서 설정
./setup-ssl.sh

# 서비스 상태 확인
systemctl status ibm-doctorai
```

### 🔧 환경별 설정
```bash
# 개발 환경
export ENVIRONMENT=development

# 스테이징 환경
export ENVIRONMENT=staging  

# 프로덕션 환경
export ENVIRONMENT=production
```




###  이슈 리포팅
- **버그 리포트**: GitHub Issues 탭 이용
- **기능 요청**: Feature Request 템플릿 사용



## 📄 라이센스

이 프로젝트는 **MIT License** 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 🙏 감사의 말

### 🔧 사용된 오픈소스
- **FastAPI**: 고성능 Python 웹 프레임워크
- **React**: 사용자 인터페이스 라이브러리
- **IBM Watson**: AI 및 머신러닝 서비스
- **Docker**: 컨테이너화 플랫폼
- **MySQL**: 관계형 데이터베이스

### 👥 기여자

PM: 박세직
AI Engineer: 임명보, 김태영
FE: 김혜림
BE: 박건우

---

