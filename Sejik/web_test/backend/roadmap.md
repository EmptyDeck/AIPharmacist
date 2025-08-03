# AI 연결 시스템 프로젝트 구조 설계

## 새로운 파일 구조 제안

```
backend/
├── main.py                          # FastAPI 메인 애플리케이션
├── requirements.txt
├── Dockerfile
├── .env
├── .gitignore
│
├── api/                            # API 엔드포인트
│   ├── __init__.py
│   ├── routes.py                   # 메인 라우터
│   └── health.py                   # 헬스체크
│
├── core/                           # 핵심 설정
│   ├── __init__.py
│   ├── config.py                   # 기존 파일 유지
│   └── dependencies.py             # FastAPI 종속성
│
├── services/                       # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── ai_orchestrator.py          # AI 라우팅 메인 로직
│   ├── choice_ai_service.py        # 선택 AI 서비스
│   ├── warn_ai_service.py          # 경고 AI 서비스
│   ├── talk_ai_service.py          # 대화 AI 서비스
│   └── calendar_service.py         # 캘린더 관련 서비스
│
├── models/                         # 데이터 모델
│   ├── __init__.py
│   ├── request_models.py           # 요청 모델
│   ├── response_models.py          # 응답 모델
│   └── ai_models.py               # AI 관련 모델
│
├── utils/                          # 유틸리티
│   ├── __init__.py
│   ├── watsonx_client.py          # Watson X 클라이언트
│   ├── google_calendar_client.py   # Google Calendar 클라이언트
│   ├── text_processor.py          # 텍스트 처리 유틸
│   └── error_handler.py           # 에러 처리 유틸
│
├── agents/                         # 특화된 에이전트
│   ├── __init__.py
│   └── cal_add_agent.py           # 캘린더 추가 에이전트
│
└── temp/                          # 임시 파일 (기존 00temp_back 대체)
    ├── voice_tmp/
    ├── input.wav
    └── output.wav
```

## 주요 구성 요소별 역할

### 1. API Layer (`api/`)
- **routes.py**: 메인 엔드포인트 정의
- **health.py**: 시스템 상태 체크

### 2. Services Layer (`services/`)
- **ai_orchestrator.py**: AI 간 라우팅 및 플로우 제어
- **choice_ai_service.py**: 초기 선택 AI 처리
- **warn_ai_service.py**: 경고 AI 처리
- **talk_ai_service.py**: 대화 AI 처리
- **calendar_service.py**: 캘린더 관련 로직

### 3. Models Layer (`models/`)
- 요청/응답 데이터 구조 정의
- Pydantic 모델 사용

### 4. Utils Layer (`utils/`)
- **watsonx_client.py**: Watson X API 통합 클라이언트
- **google_calendar_client.py**: Google Calendar API 클라이언트
- **error_handler.py**: 통합 에러 처리

### 5. Agents Layer (`agents/`)
- **cal_add_agent.py**: 캘린더 일정 추가 전용 에이전트

## 메인 플로우 설계

### 1. 초기 라우팅 플로우
```
사용자 입력 → choice_ai_service → AI 선택 결과 → ai_orchestrator → 해당 서비스 라우팅
```

### 2. 각 AI 서비스별 플로우

#### Warn AI 플로우
```
warn_ai_service → watsonx_client → 부작용 설명 반환
```

#### Talk AI 플로우
```
talk_ai_service → watsonx_client → 약물 설명 반환
```

#### Calendar AI 플로우
```
calendar_service → 일정 요약 → 사용자 확인 → cal_add_agent → google_calendar_client
```

## 에러 처리 전략

### 1. AI 서비스 실패 시
- Watson X API 호출 실패: "AI 서비스 연결에 실패했습니다"
- 응답 파싱 실패: "AI 응답 처리에 실패했습니다"

### 2. 캘린더 서비스 실패 시
- Google API 인증 실패: "캘린더 서비스 인증에 실패했습니다"
- 일정 추가 실패: "일정 추가에 실패했습니다"

### 3. 일반적인 실패 처리
- 각 서비스에서 구체적인 에러 메시지와 함께 실패 원인 반환
- 로그 기록으로 디버깅 지원

## API 엔드포인트 설계

### 메인 엔드포인트
```
POST /api/v1/process
- 사용자 입력을 받아 전체 플로우 처리
```

### 개별 서비스 엔드포인트 (디버깅용)
```
POST /api/v1/choice     # 선택 AI만 테스트
POST /api/v1/warn       # 경고 AI만 테스트
POST /api/v1/talk       # 대화 AI만 테스트
POST /api/v1/calendar   # 캘린더 서비스만 테스트
```

## 설정 관리

### 환경 변수 (.env)
```
# Watson X 설정
WATSONX_CHOICE_ENDPOINT=
WATSONX_CHOICE_API_KEY=
WATSONX_WARN_ENDPOINT=
WATSONX_WARN_API_KEY=
WATSONX_TALK_ENDPOINT=
WATSONX_TALK_API_KEY=

# Google Calendar 설정
GOOGLE_CALENDAR_CREDENTIALS_PATH=
GOOGLE_CALENDAR_ID=

# 애플리케이션 설정
LOG_LEVEL=INFO
DEBUG=False
```

## 다음 단계 구현 순서

1. **기본 구조 설정**: 폴더 구조 생성 및 기본 설정
2. **Watson X 클라이언트 구현**: 공통 클라이언트 개발
3. **Choice AI 서비스**: 첫 번째 AI 라우팅 구현
4. **각 AI 서비스 구현**: warn, talk AI 서비스
5. **캘린더 서비스 구현**: cal_add_agent 및 Google API 연동
6. **API 엔드포인트 구현**: FastAPI 라우터 설정
7. **에러 처리 및 테스트**: 통합 테스트

이 구조로 진행하시겠습니까? 어떤 부분부터 구현을 시작하고 싶으신가요?