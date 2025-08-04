from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from core.config import settings
from utils.user_token_manager import token_manager
import os
import json
from typing import Optional

# 개발 환경에서 HTTPS 요구사항 우회 (프로덕션에서는 제거 필요)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

router = APIRouter()

# Google OAuth 설정
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
REDIRECT_URI = "http://localhost:8001/auth/google/callback"

def get_google_oauth_flow():
    """Google OAuth Flow 생성"""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "project_id": settings.GOOGLE_PROJECT_ID,
            "auth_uri": settings.GOOGLE_AUTH_URI,
            "token_uri": settings.GOOGLE_TOKEN_URI,
            "auth_provider_x509_cert_url": settings.GOOGLE_AUTH_PROVIDER_X509_CERT_URL,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    return flow


@router.get("/google/login", summary="Google OAuth 로그인 시작")
async def google_login(user_id: str = Query(..., description="사용자 ID")):
    """Google OAuth 인증을 시작합니다"""
    
    # 설정 검증
    if not all([
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        settings.GOOGLE_PROJECT_ID
    ]):
        raise HTTPException(
            status_code=500,
            detail="Google OAuth 설정이 .env 파일에 없습니다."
        )
    
    try:
        flow = get_google_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=user_id  # user_id를 state에 저장
        )
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "user_id": user_id,
            "message": "위 URL로 이동하여 Google 계정으로 로그인하세요."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth 플로우 생성 실패: {str(e)}"
        )


@router.get("/google/callback", summary="Google OAuth 콜백")
async def google_callback(request: Request):
    """Google OAuth 콜백을 처리합니다"""
    
    try:
        # URL에서 인증 코드와 state(user_id) 추출
        authorization_response = str(request.url)
        state = request.query_params.get('state')
        
        if not state:
            raise HTTPException(status_code=400, detail="사용자 ID가 없습니다.")
        
        user_id = state  # state에 user_id가 저장되어 있음
        
        # Flow 생성 및 토큰 교환
        flow = get_google_oauth_flow()
        flow.fetch_token(authorization_response=authorization_response)
        
        # 사용자별 토큰 저장
        credentials = flow.credentials
        success = token_manager.save_user_token(user_id, credentials)
        
        if not success:
            raise HTTPException(status_code=500, detail="토큰 저장에 실패했습니다.")
        
        # 성공 페이지 반환
        html_content = """
        <html>
            <head>
                <title>Google Calendar 인증 완료</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #4CAF50; font-size: 2em; margin-bottom: 20px; }
                    .message { font-size: 1.2em; margin-bottom: 30px; }
                    .button { background-color: #4CAF50; color: white; padding: 10px 20px; 
                             text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="success">✅ 인증 완료!</div>
                <div class="message">
                    사용자 <strong>{user_id}</strong>의 Google Calendar 연동이 성공적으로 완료되었습니다.<br>
                    이제 복약 일정을 자동으로 추가할 수 있습니다.
                </div>
                <a href="http://localhost:8001/docs" class="button">API 문서로 이동</a>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                </script>
            </body>
        </html>
        """
        
        return HTMLResponse(content=html_content.format(user_id=user_id))
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth 콜백 처리 실패: {str(e)}"
        )


@router.get("/google/status", summary="Google 인증 상태 확인")
async def google_auth_status(user_id: str = Query(..., description="사용자 ID")):
    """현재 Google 인증 상태를 확인합니다"""
    
    try:
        is_authenticated = token_manager.is_user_authenticated(user_id)
        
        if is_authenticated:
            credentials = token_manager.load_user_token(user_id)
            return {
                "user_id": user_id,
                "authenticated": True,
                "message": f"사용자 {user_id}의 Google Calendar 인증이 활성화되어 있습니다.",
                "scopes": credentials.scopes if credentials else []
            }
        else:
            return {
                "user_id": user_id,
                "authenticated": False,
                "message": f"사용자 {user_id}의 Google 인증이 필요합니다. /auth/google/login?user_id={user_id}로 이동하세요."
            }
            
    except Exception as e:
        return {
            "user_id": user_id,
            "authenticated": False,
            "message": f"인증 상태 확인 실패: {str(e)}"
        }


@router.delete("/google/logout", summary="Google 인증 해제")
async def google_logout(user_id: str = Query(..., description="사용자 ID")):
    """Google 인증을 해제합니다"""
    
    try:
        success = token_manager.delete_user_token(user_id)
        
        if success:
            return {
                "user_id": user_id,
                "success": True,
                "message": f"사용자 {user_id}의 Google 인증이 해제되었습니다."
            }
        else:
            return {
                "user_id": user_id,
                "success": False,
                "message": f"사용자 {user_id}의 인증 해제에 실패했습니다."
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"로그아웃 처리 실패: {str(e)}"
        )