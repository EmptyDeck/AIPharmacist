from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 임포트 테스트 추가
print("=== 모듈 임포트 시작 ===")
try:
    from api import chat, auth, email, file_upload
    print("✅ API 모듈들 임포트 성공")
except Exception as e:
    print(f"❌ API 모듈 임포트 실패: {e}")
    import traceback
    traceback.print_exc()

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="Dr.Watson Backend API", version="1.0.0")

# CORS 설정 (기존과 동일)
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

# 라우터 등록 테스트
print("=== 라우터 등록 시작 ===")
try:
    app.include_router(chat.router, prefix="/api", tags=["Chat"])
    print("✅ Chat 라우터 등록 성공")
except Exception as e:
    print(f"❌ Chat 라우터 등록 실패: {e}")
    import traceback
    traceback.print_exc()

try:
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    print("✅ Auth 라우터 등록 성공")
except Exception as e:
    print(f"❌ Auth 라우터 등록 실패: {e}")

try:
    app.include_router(email.router, prefix="/api", tags=["Email"])
    print("✅ Email 라우터 등록 성공")
except Exception as e:
    print(f"❌ Email 라우터 등록 실패: {e}")

try:
    app.include_router(file_upload.router, prefix="/api/files", tags=["File Upload"])
    print("✅ File Upload 라우터 등록 성공")
except Exception as e:
    print(f"❌ File Upload 라우터 등록 실패: {e}")


from api.audio import stt, tts
from api.audio import gpt
app.include_router(stt.router, prefix="/api", tags=["STT"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(gpt.router, prefix="/api")



@app.get("/")
def root():
    return {"message": "Dr.watson Backend Server", "status": "running"}

# 등록된 라우터 확인
@app.on_event("startup")
async def startup_event():
    print("=== 등록된 엔드포인트 목록 ===")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"- {list(route.methods)} {route.path}")
    print("==============================")

if __name__ == "__main__":
    import uvicorn
    print("Starting Dr.Watson Backend Server...")
    print("URL: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
