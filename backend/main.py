from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import chat, auth, email, file_upload

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="Dr.Watson Backend API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # 프론트엔드 개발 서버들
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:3001",  # React 대체 포트
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8080",  # Vue/다른 프레임워크
        "http://localhost:8081",
        "http://localhost:5173",  # Vite 개발 서버
        "http://localhost:4200",  # Angular 개발 서버

        # 프로덕션 도메인 (나중에 추가)
        # "https://your-frontend-domain.com",
        # "https://www.your-frontend-domain.com",

        # AI 모델 서버 (팀원이 만든 모델)
        "http://localhost:5000",  # 로컬 AI 모델 서버
        "http://127.0.0.1:5000",
        # "http://ai-model-server-ip:5000",  # 팀원 AI 서버 IP

        # 개발/테스트용
        "*",  # 개발 단계에서만 사용 (프로덕션에서는 제거 필요)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# API 라우터들을 포함시킴
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(email.router, prefix="/api", tags=["Email"])
app.include_router(file_upload.router, prefix="/api/files",
                   tags=["File Upload"])


@app.get("/")
def root():
    return {"message": "Dr.watson Backend Server", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    print("Starting Dr.Watson Backend Server...")
    print("URL: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")

    uvicorn.run(app, host="127.0.0.1", port=8001)
