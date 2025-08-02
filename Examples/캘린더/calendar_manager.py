import os
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class GoogleCalendarManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.CALENDAR_ID = os.getenv('CALENDAR_ID')
        self.CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
        self.TOKEN_FILE = os.getenv('TOKEN_FILE')
        self.service = self.authenticate()

    def authenticate(self):
        """구글 캘린더 API 인증"""
        creds = None
        
        # 기존 토큰 파일이 있으면 로드
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
        
        # 유효하지 않은 토큰이면 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)

    def check_duplicate_event(self, title, start_time):
        """중복 일정 확인"""
        try:
            # 시작 시간 기준으로 하루 전후 검색
            time_min = (start_time - timedelta(days=1)).isoformat()
            time_max = (start_time + timedelta(days=1)).isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # 같은 제목과 시작 시간인 일정이 있는지 확인
            for event in events:
                if event.get('summary') == title:
                    event_start = event['start'].get('dateTime', event['start'].get('date'))
                    if event_start.startswith(start_time.strftime('%Y-%m-%d')):
                        return True
            return False
        except HttpError as error:
            print(f'중복 확인 중 오류 발생: {error}')
            return False

    def create_event(self, title, start_time, end_time, location='', description='', attendees=None):
        """일정 생성"""
        # 중복 확인
        if self.check_duplicate_event(title, start_time):
            print(f"⚠️  '{title}' 일정이 이미 존재합니다.")
            return None
        
        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
        }
        
        # 참석자 추가
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        try:
            event = self.service.events().insert(
                calendarId=self.CALENDAR_ID, 
                body=event
            ).execute()
            print(f'✅ 일정이 생성되었습니다: {event.get("htmlLink")}')
            return event
        except HttpError as error:
            print(f'일정 생성 중 오류 발생: {error}')
            return None

    def list_events(self, max_results=10):
        """일정 목록 조회"""
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                print('다가오는 일정이 없습니다.')
                return []
            
            print(f'\n📅 다가오는 {len(events)}개 일정:')
            for i, event in enumerate(events, 1):
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"{i}. {event['summary']} - {start}")
            
            return events
        except HttpError as error:
            print(f'일정 조회 중 오류 발생: {error}')
            return []

    def update_event(self, event_id, **kwargs):
        """일정 수정"""
        try:
            # 기존 일정 정보 가져오기
            event = self.service.events().get(
                calendarId=self.CALENDAR_ID, 
                eventId=event_id
            ).execute()
            
            # 수정할 내용 업데이트
            for key, value in kwargs.items():
                if key == 'title':
                    event['summary'] = value
                elif key == 'start_time':
                    event['start']['dateTime'] = value.isoformat()
                elif key == 'end_time':
                    event['end']['dateTime'] = value.isoformat()
                elif key in ['location', 'description']:
                    event[key] = value
            
            updated_event = self.service.events().update(
                calendarId=self.CALENDAR_ID,
                eventId=event_id,
                body=event
            ).execute()
            
            print(f'✅ 일정이 수정되었습니다: {updated_event.get("summary")}')
            return updated_event
        except HttpError as error:
            print(f'일정 수정 중 오류 발생: {error}')
            return None

    def delete_event(self, event_id):
        """일정 삭제"""
        try:
            self.service.events().delete(
                calendarId=self.CALENDAR_ID,
                eventId=event_id
            ).execute()
            print('✅ 일정이 삭제되었습니다.')
            return True
        except HttpError as error:
            print(f'일정 삭제 중 오류 발생: {error}')
            return False

def get_user_input():
    """사용자로부터 일정 정보 입력받기"""
    title = input("일정 제목: ")
    
    # 시작 시간 입력
    start_date = input("시작 날짜 (YYYY-MM-DD): ")
    start_time = input("시작 시간 (HH:MM): ")
    start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    
    # 종료 시간 입력
    duration = int(input("일정 시간 (시간): ") or "1")
    end_datetime = start_datetime + timedelta(hours=duration)
    
    location = input("장소 (선택사항): ")
    description = input("설명 (선택사항): ")
    
    attendees_input = input("참석자 이메일 (쉼표로 구분, 선택사항): ")
    attendees = [email.strip() for email in attendees_input.split(',')] if attendees_input else None
    
    return title, start_datetime, end_datetime, location, description, attendees

def main():
    """메인 프로그램"""
    calendar = GoogleCalendarManager()
    
    while True:
        print("\n" + "="*50)
        print("📅 구글 캘린더 관리 프로그램")
        print("="*50)
        print("1. 일정 추가")
        print("2. 일정 목록 보기")
        print("3. 일정 수정")
        print("4. 일정 삭제")
        print("5. 종료")
        
        choice = input("\n선택하세요 (1-5): ")
        
        if choice == '1':
            print("\n📝 새 일정 추가")
            title, start_time, end_time, location, description, attendees = get_user_input()
            calendar.create_event(title, start_time, end_time, location, description, attendees)
        
        elif choice == '2':
            print("\n📋 일정 목록")
            calendar.list_events()
        
        elif choice == '3':
            print("\n✏️  일정 수정")
            events = calendar.list_events()
            if events:
                try:
                    index = int(input("수정할 일정 번호: ")) - 1
                    event_id = events[index]['id']
                    
                    print("수정할 내용을 입력하세요 (엔터만 누르면 기존값 유지):")
                    new_title = input("새 제목: ")
                    
                    update_data = {}
                    if new_title:
                        update_data['title'] = new_title
                    
                    calendar.update_event(event_id, **update_data)
                except (ValueError, IndexError):
                    print("올바르지 않은 번호입니다.")
        
        elif choice == '4':
            print("\n🗑️  일정 삭제")
            events = calendar.list_events()
            if events:
                try:
                    index = int(input("삭제할 일정 번호: ")) - 1
                    event_id = events[index]['id']
                    
                    confirm = input("정말 삭제하시겠습니까? (y/N): ")
                    if confirm.lower() == 'y':
                        calendar.delete_event(event_id)
                except (ValueError, IndexError):
                    print("올바르지 않은 번호입니다.")
        
        elif choice == '5':
            print("프로그램을 종료합니다.")
            break
        
        else:
            print("올바르지 않은 선택입니다.")

if __name__ == '__main__':
    main()
