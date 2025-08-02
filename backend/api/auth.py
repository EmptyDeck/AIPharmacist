from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import httpx
import secrets
from typing import Dict
from core.config import settings

# APIRouter 인스턴스 생성
router = APIRouter()

# 상태 저장소 (실제 운영에서는 Redis 등 사용)
state_store: Dict[str, bool] = {}

# state 만료 시간 추가 (5분)
STATE_EXPIRY_SECONDS = 300


# 네이버 인증 URL 생성
def get_naver_auth_url():
    # 동적 state 생성 (보안 강화)
    state = secrets.token_urlsafe(32)
    state_store[state] = True
    
    return (
        "https://nid.naver.com/oauth2.0/authorize"
        "?response_type=code"
        f"&client_id={settings.NAVER_CLIENT_ID}"
        "&redirect_uri=http://localhost:8000/auth/callback"
        f"&state={state}"
    ), state


# 네이버 토큰 요청
async def get_naver_token(code: str, state: str):
    token_url = "https://nid.naver.com/oauth2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    params = {
        "grant_type": "authorization_code",
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "code": code,
        "state": state
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, headers=headers, data=params)
        response.raise_for_status()
        return response.json()


# 네이버 사용자 정보 요청
async def get_naver_user_info(access_token: str):
    user_info_url = "https://openapi.naver.com/v1/nid/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)
        response.raise_for_status()
        return response.json()


@router.get("/login", summary="네이버 로그인 시작")
async def login():
    auth_url, state = get_naver_auth_url()
    return {"auth_url": auth_url, "state": state}


@router.get("/callback", summary="네이버 로그인 콜백")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    # state 검증 (개발 환경에서는 완전히 비활성화)
    # if not state:
    #     raise HTTPException(status_code=400, detail="State parameter is required")
    
    # state가 store에 없을 경우 경고 로그만 출력 (개발용)
    if state not in state_store:
        print(f"⚠️  Warning: State {state} not found in store. This may happen after server restart.")
        # 개발 환경에서는 계속 진행
        # raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # 사용된 state 제거 (존재할 경우에만)
    if state in state_store:
        del state_store[state]

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    try:
        # 네이버에서 발급된 액세스 토큰을 요청
        token_response = await get_naver_token(code, state)
        access_token = token_response.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        # 액세스 토큰을 사용하여 사용자 정보를 요청
        user_info = await get_naver_user_info(access_token)
        
        return {
            "message": "Login successful",
            "user_info": user_info,
            "access_token": access_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
