from fastapi import FastAPI
from api import chat, auth, email

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="Dr.Watson Backend API", version="1.0.0")

# API 라우터들을 포함시킴
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(email.router, prefix="/api", tags=["Email"])

@app.get("/")
def root():
    return {"message": "Dr.watson Backend Server", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Dr.Watson Backend Server...")
    print("URL: http://localhost:8001")
    print("API Docs: http://localhost:8001/docs")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)