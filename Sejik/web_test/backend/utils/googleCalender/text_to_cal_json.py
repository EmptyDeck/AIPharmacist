import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.config import settings

class TextToCalendarJSON:
    def __init__(self):
        self.api_key = settings.WATSONX_API_KEY
        self.endpoint = (
            "https://us-south.ml.cloud.ibm.com/ml/v1/deployments/18d4a2e6-add0-4215-a0cb-c67ab4130f90/text/generation?version=2021-05-01"
        )
        self.token = self._get_token()
    
    def _get_token(self) -> str:
        """IBM Cloud 인증 토큰 획득"""
        try:
            res = requests.post(
                'https://iam.cloud.ibm.com/identity/token',
                data={
                    "apikey": self.api_key,
                    "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'
                },
                timeout=30
            )
            res.raise_for_status()
            return res.json()["access_token"]
        except requests.RequestException as e:
            raise Exception(f"토큰 획득 실패: {str(e)}")

    def _parse_json_response(self, text: str) -> dict:
        """AI 응답에서 JSON 추출 (개선된 버전)"""
        try:
            # "일정끝" 이전의 텍스트만 추출
            if "일정끝" in text:
                text = text.split("일정끝")[0]
            
            # JSON 부분만 추출
            start_idx = text.find('{')
            if start_idx == -1:
                raise ValueError("JSON 시작 부분을 찾을 수 없습니다.")
            
            # 중첩된 브래킷을 고려한 JSON 끝 찾기
            bracket_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    bracket_count += 1
                elif text[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            
            if bracket_count != 0:
                raise ValueError("JSON 형식이 올바르지 않습니다.")
            
            json_str = text[start_idx:end_idx]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 오류: {str(e)}\n원본 텍스트: {text[:500]}...")
        except Exception as e:
            raise Exception(f"응답 파싱 중 오류: {str(e)}")

    def _convert_watsonx_to_google_format(self, parsed_data: dict) -> List[dict]:
        """Watson X 응답을 Google Calendar 형식으로 변환"""
        events = []
        
        # Watson X 응답 구조에 맞게 수정
        calendar_events = parsed_data.get('calendar_events', [])
        
        if not calendar_events:
            # 대체 방법: medications 데이터로부터 이벤트 생성
            medications = parsed_data.get('medications', [])
            schedule_info = parsed_data.get('schedule_info', {})
            
            for med in medications:
                med_events = self._create_events_from_medication(med, schedule_info)
                events.extend(med_events)
        else:
            # Watson X에서 이미 생성된 이벤트 사용
            for event in calendar_events:
                # 필요한 경우 날짜를 현재 날짜 기준으로 조정
                adjusted_event = self._adjust_event_dates(event)
                events.append(adjusted_event)
        
        return events

    def _create_events_from_medication(self, medication: dict, schedule_info: dict) -> List[dict]:
        """약물 정보로부터 캘린더 이벤트 생성"""
        events = []
        med_name = medication.get('name', '약물')
        times = medication.get('times', ['09:00'])
        duration_days = schedule_info.get('duration_days', 7)
        
        # 시작 날짜는 오늘로 설정
        start_date = datetime.now().date()
        
        for time_str in times:
            try:
                # 시간 파싱
                hour, minute = map(int, time_str.split(':'))
                start_datetime = datetime.combine(start_date, datetime.min.time().replace(hour=hour, minute=minute))
                end_datetime = start_datetime + timedelta(minutes=30)
                
                event = {
                    'summary': f'💊 {med_name} 복용',
                    'description': f'약물: {med_name}\n복용 시간: {time_str}\n⚠️ 정확한 시간에 복용하세요!',
                    'start': {
                        'dateTime': start_datetime.strftime('%Y-%m-%dT%H:%M:00+09:00'),
                        'timeZone': 'Asia/Seoul'
                    },
                    'end': {
                        'dateTime': end_datetime.strftime('%Y-%m-%dT%H:%M:00+09:00'),
                        'timeZone': 'Asia/Seoul'
                    },
                    'recurrence': [
                        f'RRULE:FREQ=DAILY;COUNT={duration_days}'
                    ],
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 10},
                            {'method': 'popup', 'minutes': 0}
                        ]
                    }
                }
                events.append(event)
            except (ValueError, IndexError) as e:
                print(f"시간 파싱 오류 ({time_str}): {str(e)}")
                continue
        
        return events

    def _adjust_event_dates(self, event: dict) -> dict:
        """이벤트 날짜를 현재 날짜 기준으로 조정"""
        try:
            # 기존 날짜 파싱
            start_dt_str = event['start']['dateTime']
            # ISO 형식에서 날짜/시간 분리
            if 'T' in start_dt_str:
                date_part, time_part = start_dt_str.split('T')
                time_part = time_part.split('+')[0]  # 타임존 제거
                
                # 오늘 날짜로 변경
                today = datetime.now().date()
                new_start = f"{today}T{time_part}+09:00"
                
                # 종료 시간도 조정
                end_dt_str = event['end']['dateTime']
                if 'T' in end_dt_str:
                    _, end_time_part = end_dt_str.split('T')
                    end_time_part = end_time_part.split('+')[0]
                    new_end = f"{today}T{end_time_part}+09:00"
                    
                    event['start']['dateTime'] = new_start
                    event['end']['dateTime'] = new_end
        except Exception as e:
            print(f"날짜 조정 중 오류: {str(e)}")
        
        return event

    def convert_to_calendar_json(self, medication_text: str) -> dict:
        """약물 복용 정보를 구글 캘린더 JSON 형식으로 변환"""
        payload = {
            "parameters": {
                "prompt_variables": {
                    "default": medication_text
                }
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }
        
        try:
            print(f"API 요청 중: {medication_text}")
            
            response = requests.post(
                self.endpoint, 
                json=payload, 
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('results', [{}])[0].get('generated_text', '')
            
            if not generated_text:
                raise Exception("AI로부터 응답을 받지 못했습니다.")
            
            print(f"AI 응답: {generated_text[:200]}...")
            
            # JSON 파싱
            parsed_data = self._parse_json_response(generated_text)
            
            # Google Calendar 형식으로 변환
            google_events = self._convert_watsonx_to_google_format(parsed_data)
            
            return {
                "success": True,
                "original_text": medication_text,
                "ai_response": generated_text,
                "parsed_info": parsed_data,
                "google_events": google_events,
                "event_count": len(google_events)
            }
        
        except requests.RequestException as e:
            error_msg = f"API 요청 오류: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "original_text": medication_text,
                "google_events": []
            }
        
        except Exception as e:
            error_msg = f"처리 중 오류: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "original_text": medication_text,
                "google_events": []
            }

    def validate_result(self, result: dict) -> bool:
        """결과 검증"""
        if not result.get('success'):
            return False
        
        events = result.get('google_events', [])
        if not events:
            return False
        
        # 각 이벤트가 필수 필드를 가지고 있는지 확인
        required_fields = ['summary', 'start', 'end']
        for event in events:
            if not all(field in event for field in required_fields):
                return False
        
        return True

# 테스트 및 디버깅을 위한 함수
def test_converter():
    """테스트 함수"""
    converter = TextToCalendarJSON()
    
    test_cases = [
        "타이레놀 500mg 하루 3회 복용하세요. 아침, 점심, 저녁 식후에 드시면 됩니다. 감기 증상이 완전히 나을 때까지 복용해주세요.",
        "항생제는 하루 한 번, 자기 전에 드시면 됩니다. 3일간 복용해주세요",
        "시메티딘 400mg 하루 2회 점심저녁, 오늘부터 3일간",
        "오메프라졸 20mg 아침 식전에 2주간"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== 테스트 케이스 {i} ===")
        print(f"입력: {test_case}")
        
        result = converter.convert_to_calendar_json(test_case)
        
        print(f"성공: {result['success']}")
        
        if result['success']:
            print(f"이벤트 개수: {result['event_count']}")
            print(f"검증 결과: {converter.validate_result(result)}")
            
            if result['google_events']:
                first_event = result['google_events'][0]
                print(f"첫 번째 이벤트 제목: {first_event.get('summary', 'N/A')}")
                print(f"시작 시간: {first_event.get('start', {}).get('dateTime', 'N/A')}")
        else:
            print(f"오류: {result.get('error', 'Unknown error')}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_converter()