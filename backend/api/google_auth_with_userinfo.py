from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from core.config import settings
from utils.googleToken.user_token_manager import token_manager
import os
import json
from typing import Optional

# 개발 환경에서 HTTPS 요구사항 우회 (프로덕션에서는 제거 필요)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

router = APIRouter()

# Google OAuth 설정 (사용자 정보 포함)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email'
]
REDIRECT_URI = f"http://localhost:{os.getenv('PORT', '8001')}/auth/google/callback-enhanced"

def get_google_oauth_flow():
    """Google OAuth Flow 생성 (사용자 정보 포함)"""
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


@router.get("/google/login-enhanced", summary="Google OAuth 로그인 (사용자 정보 자동 획득)")
async def google_login_enhanced():
    """Google OAuth 인증을 시작합니다 (사용자 정보 자동 획득)"""
    
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
            prompt='consent'
        )
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "message": "위 URL로 이동하여 Google 계정으로 로그인하세요. 사용자 정보를 자동으로 획득합니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth 플로우 생성 실패: {str(e)}"
        )


@router.get("/google/callback-enhanced", summary="Google OAuth 콜백 (사용자 정보 자동 획득)")
async def google_callback_enhanced(request: Request):
    """Google OAuth 콜백을 처리하고 사용자 정보를 자동으로 획득합니다"""
    
    try:
        # URL에서 인증 코드 추출
        authorization_response = str(request.url)
        
        # Flow 생성 및 토큰 교환
        flow = get_google_oauth_flow()
        flow.fetch_token(authorization_response=authorization_response)
        
        # 사용자 정보 가져오기
        credentials = flow.credentials
        
        # Google API 클라이언트로 사용자 정보 조회
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        # 사용자 ID로 이메일 사용 (또는 Google ID)
        user_id = user_info.get('email', user_info.get('id', 'unknown_user'))
        user_name = user_info.get('name', 'Unknown User')
        
        # 사용자별 토큰 저장
        success = token_manager.save_user_token(user_id, credentials)
        
        if not success:
            raise HTTPException(status_code=500, detail="토큰 저장에 실패했습니다.")
        
        # 성공 페이지 반환
        html_content = f"""
        <html>
            <head>
                <title>Google Calendar 인증 완료</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #4CAF50; font-size: 2em; margin-bottom: 20px; }}
                    .message {{ font-size: 1.2em; margin-bottom: 30px; }}
                    .info {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; 
                             text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="success">✅ 인증 완료!</div>
                <div class="message">
                    <strong>{user_name}</strong>님의 Google Calendar 연동이 성공적으로 완료되었습니다!
                </div>
                
                <div class="info">
                    <h3>📋 사용자 정보</h3>
                    <p><strong>이름:</strong> {user_name}</p>
                    <p><strong>이메일:</strong> {user_id}</p>
                    <p><strong>User ID:</strong> {user_id}</p>
                </div>
                
                <div class="message">
                    이제 복약 일정을 자동으로 추가할 수 있습니다.<br>
                    API 호출 시 <code>user_id: "{user_id}"</code>를 사용하세요.
                </div>
                
                <a href="http://localhost:8001/docs" class="button">API 문서로 이동</a>
                
                <script>
                    // 클립보드에 user_id 복사 기능
                    function copyUserId() {{
                        navigator.clipboard.writeText('{user_id}');
                        alert('User ID가 클립보드에 복사되었습니다!');
                    }}
                </script>
                
                <br><br>
                <button onclick="copyUserId()" style="padding: 10px 20px; margin-top: 10px;">
                    📋 User ID 복사
                </button>
            </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth 콜백 처리 실패: {str(e)}"
        )


@router.get("/users/list", summary="인증된 사용자 목록")
async def get_authenticated_users():
    """인증된 모든 사용자 목록을 반환합니다"""
    
    try:
        users = token_manager.get_all_authenticated_users()
        
        return {
            "authenticated_users_count": len(users),
            "users": users,
            "message": f"{len(users)}명의 사용자가 인증되어 있습니다."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용자 목록 조회 실패: {str(e)}"
        )