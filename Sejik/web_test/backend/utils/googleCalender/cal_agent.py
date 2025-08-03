import os
import json
import pytz
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from core.config import settings

class CalendarAddAgent:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.CALENDAR_ID = '46e21dc8a28efb4888bf952ff88cd1514cf5dbea9faeb15615b75c1391cc2bc1@group.calendar.google.com'
        self.CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')
        self.TOKEN_FILE = os.getenv('TOKEN_FILE', 'token.json')
        self.KOREA_TZ = pytz.timezone('Asia/Seoul')
        self.service = None
        
        # 구글 캘린더 서비스 초기화 시도
        try:
            self.service = self.authenticate()
        except Exception as e:
            print(f"구글 캘린더 인증 실패: {e}")
            self.service = None
    
    def authenticate(self):
        """구글 캘린더 API 인증"""
        creds = None
        
        # 기존 토큰 파일이 있으면 로드
        if os.path.exists(self.TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
            except (json.JSONDecodeError, ValueError):
                print("토큰 파일이 손상되어 다시 인증합니다.")
                if os.path.exists(self.TOKEN_FILE):
                    os.remove(self.TOKEN_FILE)
                creds = None
        
        # 유효하지 않은 토큰이면 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    raise FileNotFoundError(f"구글 OAuth 인증 파일 {self.CREDENTIALS_FILE}을 찾을 수 없습니다.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)
    
    def add_medication_schedule(self, calendar_events: list) -> dict:
        """약물 복용 일정을 구글 캘린더에 추가 (recurrence 사용)"""
        if not self.service:
            return {
                "success": False,
                "error": "구글 캘린더 서비스에 연결할 수 없습니다.",
                "added_events": []
            }
        
        added_events = []
        failed_events = []
        
        print(f"📅 {len(calendar_events)}개의 약물 복용 시리즈를 추가하는 중...")
        
        for i, event in enumerate(calendar_events):
            try:
                # 중복 확인 (첫 번째 일정만 확인)
                if self._check_duplicate_event(event):
                    print(f"⚠️  중복된 일정 시리즈를 건너뜁니다: {event['summary']}")
                    continue
                
                # 이벤트 생성 (recurrence가 포함된 반복 일정)
                created_event = self.service.events().insert(
                    calendarId=self.CALENDAR_ID,
                    body=event
                ).execute()
                
                # recurrence 정보 추출
                recurrence_info = "단일 일정"
                if event.get('recurrence'):
                    recurrence_rule = event['recurrence'][0]
                    if 'COUNT=' in recurrence_rule:
                        count = recurrence_rule.split('COUNT=')[1].split(';')[0]
                        recurrence_info = f"{count}회 반복"
                    elif 'UNTIL=' in recurrence_rule:
                        recurrence_info = "기간 반복"
                
                added_events.append({
                    "title": created_event['summary'],
                    "start": created_event['start']['dateTime'],
                    "id": created_event['id'],
                    "link": created_event.get('htmlLink', ''),
                    "recurrence": recurrence_info,
                    "series": True  # 시리즈임을 표시
                })
                
                # 진행 상황만 간단히 출력
                print(f"📋 시리즈 {i+1}/{len(calendar_events)}: {created_event['summary']} ({recurrence_info})")
                
            except HttpError as error:
                error_msg = f"일정 추가 실패: {event['summary']} - {error}"
                print(f"❌ {error_msg}")
                failed_events.append({
                    "event": event['summary'],
                    "error": str(error)
                })
            except Exception as e:
                error_msg = f"예상치 못한 오류: {event['summary']} - {e}"
                print(f"❌ {error_msg}")
                failed_events.append({
                    "event": event.get('summary', 'Unknown'),
                    "error": str(e)
                })
        
        # 전체 결과 요약 출력
        if added_events:
            print(f"\n✅ 총 {len(added_events)}개의 약물 복용 시리즈가 성공적으로 추가되었습니다!")
            print("📅 각 시리즈는 연속된 일정으로 설정되어 한번에 관리할 수 있습니다.")
            
            for event in added_events:
                print(f"   • {event['title']} - {event['recurrence']}")
        
        if failed_events:
            print(f"\n⚠️  {len(failed_events)}개 일정 시리즈 추가 실패")
        
        return {
            "success": len(added_events) > 0,
            "added_count": len(added_events),
            "failed_count": len(failed_events),
            "added_events": added_events,
            "failed_events": failed_events,
            "message": f"{len(added_events)}개 일정 시리즈가 성공적으로 추가되었습니다."
        }

    
    def _check_duplicate_event(self, event: dict) -> bool:
        """중복 이벤트 확인"""
        try:
            start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            
            # 하루 전후로 검색
            time_min = (start_time - timedelta(days=1)).isoformat()
            time_max = (start_time + timedelta(days=1)).isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            existing_events = events_result.get('items', [])
            
            # 같은 제목과 시간인 일정 확인
            for existing_event in existing_events:
                if (existing_event.get('summary') == event['summary'] and
                    existing_event['start'].get('dateTime', '').startswith(start_time.strftime('%Y-%m-%d'))):
                    return True
            
            return False
            
        except Exception:
            # 중복 확인 실패시 안전하게 False 반환 (일정 생성 진행)
            return False
    
    def process_medication_request(self, medication_text: str) -> dict:
        """약물 복용 요청을 처리하는 메인 함수"""
        try:
            # 1단계: 텍스트를 캘린더 JSON으로 변환
            from .text_to_cal_json import TextToCalendarJSON
            
            converter = TextToCalendarJSON()
            conversion_result = converter.convert_to_calendar_json(medication_text)
            
            if not conversion_result.get('success'):
                return {
                    "success": False,
                    "error": "약물 정보를 캘린더 형식으로 변환할 수 없습니다.",
                    "details": conversion_result
                }
            
            # 2단계: 구글 캘린더에 추가
            calendar_result = self.add_medication_schedule(conversion_result['google_events'])
            
            # 3단계: 결과 종합
            return {
                "success": calendar_result['success'],
                "original_request": medication_text,
                "parsed_info": conversion_result.get('parsed_info', {}),
                "calendar_result": calendar_result,
                "summary": self._create_summary_message(conversion_result, calendar_result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"약물 캘린더 추가 처리 중 오류: {str(e)}",
                "original_request": medication_text
            }
    
    def _create_summary_message(self, conversion_result: dict, calendar_result: dict) -> str:
        """결과 요약 메시지 생성"""
        if not calendar_result['success']:
            return f"❌ 캘린더 추가에 실패했습니다.\n오류: {calendar_result.get('error', '알 수 없는 오류')}"
        
        parsed_info = conversion_result.get('parsed_info', {})
        medication_name = parsed_info.get('medication_name', '약물')
        duration_days = parsed_info.get('duration_days', 0)
        added_count = calendar_result['added_count']
        
        message = f"""✅ 약물 복용 일정이 성공적으로 추가되었습니다!

📋 약물 정보:
- 약물명: {medication_name}
- 복용 기간: {duration_days}일
- 추가된 알림: {added_count}개

📅 구글 캘린더에서 복용 알림을 확인하실 수 있습니다."""

        if calendar_result['failed_count'] > 0:
            message += f"\n\n⚠️  {calendar_result['failed_count']}개 일정은 추가되지 않았습니다."
        
        return message

# 테스트
if __name__ == "__main__":
    try:
        agent = CalendarAddAgent()
        
        test_requests = [
            "타이레놀 500mg 하루 3번 아침점심저녁으로 3일간",
            "오메프라졸 20mg 아침 식전에 일주일간"
        ]
        
        for request in test_requests:
            print(f"\n{'='*60}")
            print(f"처리 요청: {request}")
            print('='*60)
            
            result = agent.process_medication_request(request)
            
            print(f"성공 여부: {result['success']}")
            if result['success']:
                print(result['summary'])
            else:
                print(f"오류: {result['error']}")
            
    except Exception as e:
        print(f"테스트 실행 오류: {e}")
