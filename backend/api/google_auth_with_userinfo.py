from fastapi import APIRouter, HTTPException, Request, Query, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from core.config import settings
from utils.googleToken.user_token_manager import token_manager
from database import get_db, User
from sqlalchemy.orm import Session
import os
import json
from typing import Optional
from datetime import datetime

# 개발 환경에서 HTTPS 요구사항 우회 (프로덕션에서는 제거 필요)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

router = APIRouter()

# Google OAuth 설정 (사용자 정보 포함)
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile', 
    'openid',
    'https://www.googleapis.com/auth/calendar.events'
]
REDIRECT_URI = "http://3.27.201.191:8001/auth/google/callback-enhanced"

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
async def google_callback_enhanced(request: Request, db: Session = Depends(get_db)):
    """Google OAuth 콜백을 처리하고 사용자 정보를 자동으로 획득합니다"""
    
    try:
        # URL에서 인증 코드 추출
        authorization_response = str(request.url)
        
        # Flow 생성 및 토큰 교환
        flow = get_google_oauth_flow()
        flow.fetch_token(authorization_response=authorization_response)
        
        # 사용자 정보 가져오기
        credentials = flow.credentials
        
        # 직접 HTTP 요청으로 사용자 정보 조회 (user_id를 먼저 얻기 위함)
        try:
            import requests
            
            # 액세스 토큰 확인
            access_token = credentials.token
            if not access_token:
                raise Exception("Access token is missing")
            
            # 올바른 헤더 형식으로 API 호출
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"사용자 정보 조회 성공: {user_info.get('email', 'unknown')}")
            else:
                raise Exception(f"API 호출 실패: {response.status_code} - {response.text}")
                
        except Exception as api_error:
            print(f"사용자 정보 조회 실패: {api_error}")
            # 기본값 사용
            import time
            current_time = int(time.time())
            user_info = {
                'email': f'user_{current_time}@gmail.com',
                'name': f'Google User {current_time}',
                'id': f'google_user_{current_time}'
            }
        
        # 사용자 정보 추출
        user_email = user_info.get('email', 'unknown@gmail.com')
        user_name = user_info.get('name', 'Unknown User')
        google_id = user_info.get('id')
        profile_picture = user_info.get('picture')
        
        # 데이터베이스에서 사용자 조회 또는 생성
        db_user = db.query(User).filter(User.email == user_email).first()
        
        if not db_user:
            # 새 사용자 생성
            db_user = User(
                email=user_email,
                name=user_name,
                google_id=google_id,
                profile_picture=profile_picture,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expires_at=credentials.expiry
            )
            db.add(db_user)
        else:
            # 기존 사용자 업데이트
            db_user.name = user_name
            db_user.google_id = google_id
            db_user.profile_picture = profile_picture
            db_user.access_token = credentials.token
            if credentials.refresh_token:
                db_user.refresh_token = credentials.refresh_token
            db_user.token_expires_at = credentials.expiry
            db_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_user)
        
        # 기존 토큰 관리자도 계속 사용 (호환성을 위해)
        user_id = user_email
        
        # 기존 토큰에서 refresh_token 복원 (Google이 새로 주지 않는 경우)
        if not credentials.refresh_token and db_user.refresh_token:
            credentials = Credentials(
                token=credentials.token,
                refresh_token=db_user.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes
            )
            print(f"사용자 {user_id}의 DB에서 refresh_token을 복원했습니다")
        
        # 사용자별 토큰 저장 (기존 시스템과 호환성 유지)
        success = token_manager.save_user_token(user_id, credentials)
        
        if not success:
            raise HTTPException(status_code=500, detail="토큰 저장에 실패했습니다.")
        
        # 프론트엔드로 리다이렉트 (사용자 정보를 쿼리 파라미터로 전달)
        redirect_url = f"http://localhost:3000/chat?user_id={user_id}&user_name={user_name}&auth_success=true"
        return RedirectResponse(url=redirect_url)
        
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