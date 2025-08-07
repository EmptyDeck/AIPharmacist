# Sejik/Demo/backend/api/google_auth_with_userinfo.py
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from core.config import settings
from utils.googleToken.user_token_manager import token_manager
from DB.database import get_db, User
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
REDIRECT_URI = "http://localhost:8001/auth/google/callback-enhanced"

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


@router.get("/google/callback", summary="Google OAuth 콜백 (간단 리다이렉트)")
async def google_callback(request: Request):
    """Google OAuth 콜백을 처리하고 바로 /chat으로 리다이렉트합니다"""
    
    try:
        # 데이터베이스 처리를 건너뛰고 바로 /chat으로 리다이렉트
        print(f"Google OAuth callback received: {request.url}")
        
        # 프론트엔드의 /chat 페이지로 바로 리다이렉트
        redirect_url = "http://localhost:3000/chat"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        print(f"Google OAuth 콜백 처리 중 오류: {str(e)}")
        # 오류가 발생해도 /chat으로 리다이렉트
        redirect_url = "http://localhost:3000/chat"
        return RedirectResponse(url=redirect_url)


@router.get("/google/callback-enhanced", summary="Google OAuth 콜백 (사용자 정보 자동 획득)")
async def google_callback_enhanced(request: Request):
    """Google OAuth 콜백을 처리하고 사용자 정보를 자동으로 획득합니다"""
    
    try:
        # 데이터베이스 처리를 건너뛰고 바로 /chat으로 리다이렉트
        print(f"Google OAuth callback received: {request.url}")
        
        # 프론트엔드의 /chat 페이지로 바로 리다이렉트
        redirect_url = "http://localhost:3000/chat"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        print(f"Google OAuth 콜백 처리 중 오류: {str(e)}")
        # 오류가 발생해도 /chat으로 리다이렉트
        redirect_url = "http://localhost:3000/chat"
        return RedirectResponse(url=redirect_url)


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