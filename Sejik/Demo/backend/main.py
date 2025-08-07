# Sejik/Demo/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import traceback

print("=== [1] 모듈 임포트 시작 ===")
# API 라우터 모듈 임포트
try:
    from api import chat, auth, email, file_upload, calendar, google_auth_with_userinfo, users, voice
    print("✅ API 라우터 임포트 성공")
except Exception as e:
    print(f"❌ [Critical] API 라우터 모듈 임포트 실패: {e}")
    traceback.print_exc()

# audio 관련 모듈도 필요한 경우 try/except 추가
try:
    from api.audio import stt, tts, gpt
    print("✅ Audio 모듈 임포트 성공")
except Exception as e:
    print(f"❌ Audio 모듈 임포트 실패: {e}")

# DB create_tables
try:
    from DB.database import create_tables
    create_tables()
    print("✅ DB 테이블 생성 성공")
except Exception as e:
    print(f"❌ DB 테이블 생성 실패: {e}")
    traceback.print_exc()


# FastAPI 인스턴스
app = FastAPI(title="Dr.Watson Backend API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:5173",
        "http://localhost:4200",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

print("=== [2] 라우터 등록 시작 ===")
def safe_router(router, prefix, tags):
    try:
        app.include_router(router, prefix=prefix, tags=tags)
        print(f"✅ 라우터 등록 성공: {tags} ({prefix})")
    except Exception as e:
        print(f"❌ 라우터 등록 실패: {tags} ({prefix}) | {e}")
        traceback.print_exc()

safe_router(chat.router, "/api", ["Chat"])
safe_router(auth.router, "/auth", ["Authentication"])
safe_router(email.router, "/api", ["Email"])
safe_router(file_upload.router, "/api/files", ["File Upload"])
safe_router(calendar.router, "/api/calendar", ["Calendar"])
safe_router(google_auth_with_userinfo.router, "/auth", ["Google Auth User Info"])
safe_router(users.router, "/api", ["User CRUD"])
#safe_router(voice.router, "/api", ["Voice"])

# 필요시 audio 관련 라우터도 등록  
safe_router(stt.router, "/api", ["STT"])
safe_router(tts.router, "/api", ["TTS"])
safe_router(gpt.router, "/api", ["GPT"])


@app.get("/")
def root():
    return {"message": "Dr.watson Backend Server", "status": "running"}


@app.on_event("startup")
async def startup_event():
    print("=== [3] 등록된 엔드포인트 목록 ===")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"- {list(route.methods)} {route.path}")
    print("==============================")

"""로컬 테스트용"""
if __name__ == "__main__":
    import uvicorn
    print("Starting Dr.Watson Backend Server...")
    print("URL: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    uvicorn.run(app, host="127.0.0.1", port=8001)
