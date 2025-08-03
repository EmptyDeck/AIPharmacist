import requests
import json
from datetime import datetime, timedelta
from core.config import settings

class TextToCalendarJSON:
    def __init__(self):
        # core.config의 settings 사용
        self.api_key = settings.WATSONX_API_KEY
        # 새로운 엔드포인트 사용
        self.endpoint = "https://us-south.ml.cloud.ibm.com/ml/v1/deployments/18d4a2e6-add0-4215-a0cb-c67ab4130f90/text/generation?version=2021-05-01"
        self.token = self._get_token()
    
    def _get_token(self):
        """IBM Cloud IAM 토큰 획득"""
        token_response = requests.post(
            'https://iam.cloud.ibm.com/identity/token', 
            data={
                "apikey": self.api_key, 
                "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'
            }
        )
        return token_response.json()["access_token"]
    
    def convert_to_calendar_json(self, medication_text: str) -> dict:
        """약물 복용 정보를 구글 캘린더 JSON 형식으로 변환"""
        
        # IBM Watson에 보낼 프롬프트 (예시 참고)
        prompt = f"{medication_text}"

        payload = {
            "parameters": {
                "prompt_variables": {
                    "default": medication_text
                },
                "max_new_tokens": 500,
                "temperature": 0.1,  # 정확한 JSON을 위해 낮은 온도
                "top_p": 0.9
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('results', [{}])[0].get('generated_text', '')
            
            # JSON 추출 및 파싱
            calendar_json = self._parse_json_response(generated_text)
            
            # 현재 날짜로 시작 날짜 설정 (AI가 설정하지 않은 경우)
            if not calendar_json.get('start_date'):
                calendar_json['start_date'] = datetime.now().strftime('%Y-%m-%d')
            
            # 구글 캘린더 형식으로 최종 변환
            google_calendar_events = self._convert_to_google_format(calendar_json)
            
            return {
                "success": True,
                "original_text": medication_text,
                "parsed_info": calendar_json,
                "google_events": google_calendar_events
            }
            
        except Exception as e:
            print(f"JSON 변환 오류: {str(e)}")
            # 실패시 기본 형식으로 fallback
            return self._create_fallback_json(medication_text)
    
    def _parse_json_response(self, text: str) -> dict:
        """AI 응답에서 JSON 추출"""
        try:
            # JSON 부분만 추출
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("JSON 형식을 찾을 수 없습니다.")
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            raise Exception(f"AI 응답을 JSON으로 파싱할 수 없습니다: {text[:200]}...")
    
    def _convert_to_google_format(self, calendar_json: dict) -> list:
        """파싱된 정보를 구글 캘린더 이벤트 형식으로 변환"""
        events = []
        
        medication_name = calendar_json.get('medication_name', '약물')
        dosage = calendar_json.get('dosage', '')
        times = calendar_json.get('times', ['09:00'])
        duration_days = calendar_json.get('duration_days', 7)
        start_date = datetime.strptime(calendar_json.get('start_date'), '%Y-%m-%d')
        instructions = calendar_json.get('instructions', '')
        
        # 각 복용 시간에 대해 이벤트 생성
        for time_str in times:
            try:
                hour, minute = map(int, time_str.split(':'))
            except:
                hour, minute = 9, 0  # 기본값
            
            # 기간 동안 매일 이벤트 생성
            for day in range(duration_days):
                event_date = start_date + timedelta(days=day)
                start_datetime = event_date.replace(hour=hour, minute=minute)
                end_datetime = start_datetime + timedelta(minutes=15)  # 15분 알림
                
                event = {
                    'summary': f'{medication_name} 복용',
                    'description': f'{dosage}\n{instructions}\n\n자동 생성된 약물 복용 알림',
                    'start': {
                        'dateTime': start_datetime.strftime('%Y-%m-%dT%H:%M:00'),
                        'timeZone': 'Asia/Seoul',
                    },
                    'end': {
                        'dateTime': end_datetime.strftime('%Y-%m-%dT%H:%M:00'),
                        'timeZone': 'Asia/Seoul',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 10},  # 10분 전 알림
                        ],
                    },
                }
                events.append(event)
        
        return events
    
    def _create_fallback_json(self, medication_text: str) -> dict:
        """AI 파싱 실패시 기본 형식으로 생성"""
        return {
            "success": True,
            "original_text": medication_text,
            "parsed_info": {
                "medication_name": "약물 복용",
                "dosage": "처방전 확인 필요",
                "frequency": "1일 3회",
                "times": ["08:00", "12:00", "18:00"],
                "duration_days": 7,
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "instructions": medication_text
            },
            "google_events": self._convert_to_google_format({
                "medication_name": "약물 복용",
                "dosage": "처방전 확인 필요", 
                "times": ["08:00", "12:00", "18:00"],
                "duration_days": 7,
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "instructions": medication_text
            }),
            "fallback": True
        }

# 테스트
if __name__ == "__main__":
    try:
        converter = TextToCalendarJSON()
        
        test_cases = [
            "시메티딘 400mg 하루 2회 점심저녁, 오늘부터 3일간",
            "타이레놀 500mg 하루 3번 아침점심저녁으로 일주일",
            "오메프라졸 20mg 아침 식전에 2주간"
        ]
        
        for test_case in test_cases:
            print(f"입력: {test_case}")
            result = converter.convert_to_calendar_json(test_case)
            
            print(f"성공: {result['success']}")
            print(f"이벤트 개수: {len(result['google_events'])}")
            if result['google_events']:
                print(f"첫 번째 이벤트: {result['google_events'][0]['summary']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"오류: {e}")
