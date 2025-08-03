import os
import json
import pytz
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

app = Flask(__name__)

# .env 파일 로드
load_dotenv()


class WebMedicationSchedulerAgent:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.CALENDAR_ID = os.getenv('CALENDAR_ID')
        self.CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
        self.TOKEN_FILE = os.getenv('TOKEN_FILE')
        self.KOREA_TZ = pytz.timezone('Asia/Seoul')
        self.service = self.authenticate()

    def authenticate(self):
        """구글 캘린더 API 인증"""
        creds = None

        if os.path.exists(self.TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.TOKEN_FILE, self.SCOPES)
            except (json.JSONDecodeError, ValueError):
                if os.path.exists(self.TOKEN_FILE):
                    os.remove(self.TOKEN_FILE)
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=8080)

            with open(self.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)

    def parse_medication_text(self, patient_text):
        """약물 정보 텍스트 파싱"""
        medications = []

        # 다양한 패턴으로 약물 정보 추출
        patterns = {
            'pattern1': r'(\w+)\s*(?:정|캡슐|포|알|mg|g)?\s*(?:\d+(?:\.\d+)?(?:mg|g)?)\s*[\s,]*(?:하루|일일)?\s*(\d+)\s*(?:회|번)\s*(?:복용|복용하세요|드시면)',
            'pattern2': r'(\w+)\s*(?:정|캡슐|포|알)?\s*[\s,]*(?:아침|점심|저녁|식전|식후|취침전)?\s*(?:하루|일일)?\s*(\d+)\s*(?:회|번)',
            'pattern3': r'(\w+)\s*[\s,]*(?:1일|하루)\s*(\d+)\s*(?:회|번)',
            'pattern4': r'(\w+).*?(\d+)\s*시간?\s*마다',
            'pattern5': r'(\w+).*?(?:아침|점심|저녁)',
        }

        # 텍스트를 줄 단위로 분석
        lines = patient_text.replace('\n', ' ').split('.')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 각 패턴으로 매칭 시도
            for pattern_name, pattern in patterns.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)

                for match in matches:
                    med_name = match.group(1).strip()
                    if len(med_name) < 2:
                        continue

                    try:
                        frequency = int(match.group(2))
                    except:
                        frequency = 1

                    times = self.determine_medication_times(line, frequency)

                    medications.append({
                        'name': med_name,
                        'frequency': frequency,
                        'times': times,
                        'original_text': line
                    })

        # 중복 제거
        unique_medications = []
        seen_names = set()

        for med in medications:
            if med['name'] not in seen_names:
                unique_medications.append(med)
                seen_names.add(med['name'])

        return unique_medications

    def determine_medication_times(self, text, frequency):
        """텍스트 분석으로 복용 시간 결정"""
        times = []

        time_keywords = {
            '아침': '08:00',
            '점심': '12:00',
            '저녁': '18:00',
            '취침': '22:00',
            '식전': ['07:30', '11:30', '17:30'],
            '식후': ['08:30', '12:30', '18:30']
        }

        text_lower = text.lower()

        for keyword, time_list in time_keywords.items():
            if keyword in text_lower:
                if isinstance(time_list, list):
                    if frequency <= len(time_list):
                        times.extend(time_list[:frequency])
                    else:
                        times.extend(time_list)
                else:
                    times.append(time_list)

        if not times:
            default_times = {
                1: ['08:00'],
                2: ['08:00', '20:00'],
                3: ['08:00', '12:00', '20:00'],
                4: ['08:00', '12:00', '16:00', '20:00']
            }
            times = default_times.get(frequency, ['08:00', '12:00', '20:00'])

        return times[:frequency]

    def create_medication_schedule(self, medications, duration_days=30):
        """약물 복용 일정을 캘린더에 추가"""
        start_date = datetime.now(self.KOREA_TZ).date()
        created_events = []
        result_messages = []

        result_messages.append(f"🏥 약물 복용 일정을 생성합니다...")
        result_messages.append(f"📅 시작일: {start_date}")
        result_messages.append(f"⏱️ 기간: {duration_days}일")
        result_messages.append("="*50)

        for med in medications:
            result_messages.append(f"💊 {med['name']} - 하루 {med['frequency']}회")
            result_messages.append(f"⏰ 복용 시간: {', '.join(med['times'])}")

            for time_str in med['times']:
                success = self.create_recurring_medication_event(
                    med_name=med['name'],
                    time_str=time_str,
                    start_date=start_date,
                    duration_days=duration_days
                )

                if success:
                    created_events.append(f"{med['name']} at {time_str}")
                    result_messages.append(f"  ✅ {time_str} 일정 생성 완료")
                else:
                    result_messages.append(f"  ❌ {time_str} 일정 생성 실패")

        return {
            'success': True,
            'created_events': created_events,
            'messages': result_messages,
            'total_count': len(created_events)
        }

    def create_recurring_medication_event(self, med_name, time_str, start_date, duration_days):
        """반복되는 약물 복용 일정 생성"""
        try:
            hour, minute = map(int, time_str.split(':'))
            start_datetime = datetime.combine(
                start_date, datetime.min.time().replace(hour=hour, minute=minute))
            start_datetime = self.KOREA_TZ.localize(start_datetime)

            end_datetime = start_datetime + timedelta(minutes=30)
            end_date = start_date + timedelta(days=duration_days)

            event = {
                'summary': f'💊 {med_name} 복용',
                'description': f'약물: {med_name}\n복용 시간: {time_str}\n⚠️ 정확한 시간에 복용하세요!',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'recurrence': [
                    f'RRULE:FREQ=DAILY;UNTIL={end_date.strftime("%Y%m%d")}T235959Z'
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 10},
                        {'method': 'popup', 'minutes': 0},
                    ],
                },
            }

            self.service.events().insert(
                calendarId=self.CALENDAR_ID,
                body=event
            ).execute()

            return True

        except HttpError as error:
            return False

    def process_patient_text_web(self, patient_text, duration_days=30):
        """웹용 환자 텍스트 처리"""
        result = {
            'success': False,
            'messages': [],
            'medications': [],
            'created_events': []
        }

        result['messages'].append("🤖 약물 정보 분석 에이전트 시작...")
        result['messages'].append("="*60)
        result['messages'].append("📄 받은 텍스트:")
        result['messages'].append("-" * 30)
        result['messages'].append(patient_text)
        result['messages'].append("-" * 30)

        # 1. 텍스트 파싱
        medications = self.parse_medication_text(patient_text)

        if not medications:
            result['messages'].append("❌ 약물 정보를 찾을 수 없습니다.")
            result['messages'].append("💡 텍스트에 다음과 같은 정보가 포함되어야 합니다:")
            result['messages'].append("   - 약물명")
            result['messages'].append("   - 복용 횟수 (예: 하루 3회)")
            result['messages'].append("   - 복용 시간 (예: 아침, 점심, 저녁)")
            return result

        result['medications'] = medications
        result['messages'].append(f"✅ {len(medications)}개의 약물 정보를 찾았습니다:")

        for i, med in enumerate(medications, 1):
            result['messages'].append(
                f"{i}. {med['name']} - 하루 {med['frequency']}회")
            result['messages'].append(f"   복용시간: {', '.join(med['times'])}")

        # 2. 일정 생성
        schedule_result = self.create_medication_schedule(
            medications, duration_days)

        result['success'] = schedule_result['success']
        result['created_events'] = schedule_result['created_events']
        result['messages'].extend(schedule_result['messages'])
        result['messages'].append(
            f"🎉 총 {len(schedule_result['created_events'])}개의 약물 복용 일정이 생성되었습니다!")

        return result

    def get_medication_events(self):
        """약물 일정 조회"""
        try:
            now_kst = datetime.now(self.KOREA_TZ)
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                timeMin=now_kst.isoformat(),
                q='💊',
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            formatted_events = []

            for event in events:
                start = event['start'].get(
                    'dateTime', event['start'].get('date'))
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    dt_kst = dt.astimezone(self.KOREA_TZ)
                    formatted_events.append({
                        'id': event['id'],
                        'title': event['summary'],
                        'start_time': dt_kst.strftime('%m/%d %H:%M'),
                        'description': event.get('description', '')
                    })
                except:
                    pass

            return {'success': True, 'events': formatted_events}

        except HttpError as error:
            return {'success': False, 'error': str(error)}

    def delete_all_medication_events(self):
        """모든 약물 일정 삭제"""
        try:
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                q='💊',
                maxResults=500
            ).execute()

            events = events_result.get('items', [])
            deleted_count = 0

            for event in events:
                try:
                    self.service.events().delete(
                        calendarId=self.CALENDAR_ID,
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1
                except:
                    pass

            return {'success': True, 'deleted_count': deleted_count}

        except HttpError as error:
            return {'success': False, 'error': str(error)}


# 글로벌 에이전트 인스턴스
medication_agent = WebMedicationSchedulerAgent()


@app.route('/')
def index():
    return render_template('medication_scheduler.html')


@app.route('/process_medication', methods=['POST'])
def process_medication():
    try:
        data = request.get_json()
        patient_text = data.get('patient_text', '').strip()
        duration_days = data.get('duration_days', 30)

        if not patient_text:
            return jsonify({'success': False, 'error': '약물 정보를 입력해주세요.'}), 400

        result = medication_agent.process_patient_text_web(
            patient_text, duration_days)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500


@app.route('/get_events', methods=['GET'])
def get_events():
    try:
        result = medication_agent.get_medication_events()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/delete_events', methods=['POST'])
def delete_events():
    try:
        result = medication_agent.delete_all_medication_events()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
