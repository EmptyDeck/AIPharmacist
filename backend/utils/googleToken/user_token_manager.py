import os
import json
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from pathlib import Path


class UserTokenManager:
    """사용자별 Google OAuth 토큰을 관리하는 클래스"""
    
    def __init__(self, tokens_dir: str = "user_tokens"):
        self.tokens_dir = Path(tokens_dir)
        self.tokens_dir.mkdir(exist_ok=True)
    
    def get_token_file_path(self, user_id: str) -> Path:
        """사용자별 토큰 파일 경로를 반환합니다"""
        safe_user_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_'))
        return self.tokens_dir / f"google_token_{safe_user_id}.json"
    
    def save_user_token(self, user_id: str, credentials: Credentials) -> bool:
        """사용자의 Google OAuth 토큰을 저장합니다"""
        try:
            token_data = {
                'user_id': user_id,
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            token_file = self.get_token_file_path(user_id)
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"사용자 {user_id}의 토큰이 저장되었습니다: {token_file}")
            return True
            
        except Exception as e:
            print(f"토큰 저장 실패 ({user_id}): {e}")
            return False
    
    def load_user_token(self, user_id: str) -> Optional[Credentials]:
        """사용자의 Google OAuth 토큰을 로드합니다"""
        try:
            token_file = self.get_token_file_path(user_id)
            
            if not token_file.exists():
                return None
            
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            credentials = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes')
            )
            
            return credentials
            
        except Exception as e:
            print(f"토큰 로드 실패 ({user_id}): {e}")
            return None
    
    def delete_user_token(self, user_id: str) -> bool:
        """사용자의 토큰을 삭제합니다"""
        try:
            token_file = self.get_token_file_path(user_id)
            
            if token_file.exists():
                token_file.unlink()
                print(f"사용자 {user_id}의 토큰이 삭제되었습니다")
                return True
            else:
                print(f"사용자 {user_id}의 토큰 파일이 존재하지 않습니다")
                return True
                
        except Exception as e:
            print(f"토큰 삭제 실패 ({user_id}): {e}")
            return False
    
    def is_user_authenticated(self, user_id: str) -> bool:
        """사용자가 인증되어 있는지 확인합니다"""
        credentials = self.load_user_token(user_id)
        return credentials is not None and credentials.valid
    
    def get_all_authenticated_users(self) -> list:
        """인증된 모든 사용자 목록을 반환합니다"""
        authenticated_users = []
        
        for token_file in self.tokens_dir.glob("google_token_*.json"):
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                    user_id = token_data.get('user_id')
                    if user_id and self.is_user_authenticated(user_id):
                        authenticated_users.append(user_id)
            except:
                continue
                
        return authenticated_users


# 싱글톤 인스턴스
token_manager = UserTokenManager()