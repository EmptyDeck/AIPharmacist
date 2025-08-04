import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .text_to_cal_json import text_to_cal_converter
from core.config import settings
from utils.googleToken.user_token_manager import token_manager

# 개발 환경에서 HTTPS 요구사항 우회 (프로덕션에서는 제거 필요)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class GoogleCalendarAgent:
    """Google Calendar API를 사용한 복약 스케줄 관리"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.korea_tz = pytz.timezone('Asia/Seoul')
        # 사용자별 서비스 인스턴스 캐시
        self._user_services = {}
        
        # .env에서 Google OAuth 설정 가져오기
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "project_id": settings.GOOGLE_PROJECT_ID,
                "auth_uri": settings.GOOGLE_AUTH_URI,
                "token_uri": settings.GOOGLE_TOKEN_URI,
                "auth_provider_x509_cert_url": settings.GOOGLE_AUTH_PROVIDER_X509_CERT_URL,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URIS]
            }
        }
    
    def get_user_service(self, user_id: str):
        """사용자별 Google Calendar 서비스를 반환합니다"""
        
        # 캐시된 서비스가 있는지 확인
        if user_id in self._user_services:
            return self._user_services[user_id]
        
        # 사용자 토큰 로드
        credentials = token_manager.load_user_token(user_id)
        
        if not credentials:
            print(f"사용자 {user_id}의 토큰이 없습니다. 먼저 인증이 필요합니다.")
            return None
        
        # 토큰 유효성 확인 및 갱신
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                    # 갱신된 토큰 저장
                    token_manager.save_user_token(user_id, credentials)
                    print(f"사용자 {user_id}의 토큰이 갱신되었습니다.")
                except Exception as e:
                    print(f"토큰 갱신 실패 ({user_id}): {e}")
                    return None
            else:
                print(f"사용자 {user_id}의 토큰이 유효하지 않습니다. 재인증이 필요합니다.")
                return None
        
        # Google Calendar 서비스 생성
        try:
            service = build('calendar', 'v3', credentials=credentials)
            self._user_services[user_id] = service
            print(f"사용자 {user_id}의 Google Calendar 서비스 연결 성공")
            return service
        except Exception as e:
            print(f"Calendar 서비스 빌드 실패 ({user_id}): {e}")
            return None
    
    def is_user_authenticated(self, user_id: str) -> bool:
        """사용자가 인증되어 있는지 확인합니다"""
        return token_manager.is_user_authenticated(user_id)
    
    def check_existing_events(self, user_id: str, medication_name: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """중복 이벤트 확인 - 정확한 제목 매칭"""
        service = self.get_user_service(user_id)
        if not service:
            return []
        
        try:
            # 복약 이벤트 전체 조회
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                q='💊',  # 복약 이모지로 필터링
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # 정확한 제목 매칭으로 필터링
            exact_matches = []
            for event in events:
                event_summary = event.get('summary', '')
                if event_summary == f'💊 {medication_name}':
                    exact_matches.append(event)
            
            print(f"🔍 중복 체크: '{medication_name}' -> {len(exact_matches)}개 발견")
            return exact_matches
            
        except HttpError as e:
            print(f"기존 이벤트 확인 실패 ({user_id}): {e}")
            return []
    
    def add_medication_schedule(self, user_id: str, events: List[Dict]) -> Dict:
        """복약 스케줄을 Google Calendar에 추가합니다"""
        service = self.get_user_service(user_id)
        if not service:
            return {
                'success': False,
                'message': f'사용자 {user_id}의 Google Calendar 인증에 실패했습니다.',
                'events_added': 0
            }
        
        results = {
            'success': True,
            'message': '',
            'events_added': 0,
            'failed_events': [],
            'created_events': []
        }
        
        for event in events:
            try:
                # 중복 확인 (전체 제목 사용 - 시간대 구분)
                medication_name = event.get('summary', '').replace('💊 ', '')
                start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                end_time = start_time + timedelta(days=30)  # 한 달간 확인
                
                existing_events = self.check_existing_events(user_id, medication_name, start_time, end_time)
                
                if existing_events:
                    print(f"이미 존재하는 이벤트 건너뜀: {medication_name}")
                    continue
                
                # 이벤트 생성
                created_event = service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                
                results['events_added'] += 1
                results['created_events'].append({
                    'id': created_event.get('id'),
                    'summary': created_event.get('summary'),
                    'start': created_event.get('start', {}).get('dateTime'),
                    'html_link': created_event.get('htmlLink')
                })
                
            except HttpError as e:
                error_msg = f"이벤트 생성 실패: {event.get('summary', 'Unknown')} - {str(e)}"
                print(error_msg)
                results['failed_events'].append(error_msg)
                results['success'] = False
            except Exception as e:
                error_msg = f"예상치 못한 오류: {event.get('summary', 'Unknown')} - {str(e)}"
                print(error_msg)
                results['failed_events'].append(error_msg)
                results['success'] = False
        
        if results['events_added'] > 0:
            results['message'] = f"{results['events_added']}개의 복약 알림이 캘린더에 추가되었습니다."
        else:
            results['message'] = "추가된 이벤트가 없습니다."
            if results['failed_events']:
                results['message'] += f" 실패: {len(results['failed_events'])}개"
        
        return results
    
    def process_medication_request(self, user_id: str, medication_text: str, start_date: datetime = None) -> Dict:
        """복약 텍스트를 받아서 전체 파이프라인을 실행합니다"""
        
        try:
            # 1단계: 텍스트를 캘린더 이벤트로 변환
            events = text_to_cal_converter.process_medication_text(medication_text, start_date)
            
            if not events:
                return {
                    'success': False,
                    'message': '복약 정보를 처리할 수 없습니다.',
                    'events_added': 0
                }
            
            # 2단계: Google Calendar에 추가
            results = self.add_medication_schedule(user_id, events)
            
            # 결과에 처리된 이벤트 정보 추가
            results['processed_events'] = len(events)
            results['medication_text'] = medication_text
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'message': f'복약 스케줄 처리 중 오류가 발생했습니다: {str(e)}',
                'events_added': 0,
                'error': str(e)
            }
    
    def get_upcoming_medication_events(self, user_id: str, days: int = 7) -> List[Dict]:
        """다가오는 복약 일정을 가져옵니다"""
        service = self.get_user_service(user_id)
        if not service:
            return []
        
        try:
            now = datetime.now(self.korea_tz)
            time_max = now + timedelta(days=days)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                q='💊',  # 복약 이벤트 이모지로 필터링
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return [{
                'id': event.get('id'),
                'summary': event.get('summary'),
                'start': event.get('start', {}).get('dateTime'),
                'description': event.get('description', ''),
                'html_link': event.get('htmlLink')
            } for event in events]
            
        except HttpError as e:
            print(f"일정 조회 실패 ({user_id}): {e}")
            return []


# 싱글톤 인스턴스
calendar_agent = GoogleCalendarAgent()