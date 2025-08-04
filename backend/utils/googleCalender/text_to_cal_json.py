import json
from datetime import datetime, timedelta
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from core.config import settings
from typing import Optional, List, Dict
import pytz


class TextToCalendarConverter:
    """자연어 복약 지시사항을 Google Calendar 이벤트로 변환하는 클래스"""
    
    def __init__(self):
        self._model: Optional[Model] = None
        self.korea_tz = pytz.timezone('Asia/Seoul')
    
    def get_model(self) -> Model:
        """IBM Watson 모델 인스턴스를 반환합니다"""
        if self._model is None:
            creds = {
                "url": settings.WATSONX_API_URL,
                "apikey": settings.WATSONX_API_KEY
            }
            self._model = Model(
                model_id='ibm/granite-3-3-8b-instruct',
                credentials=creds,
                project_id=settings.WATSONX_PROJECT_ID
            )
        return self._model
    
    def extract_medication_info(self, medication_text: str) -> Dict:
        """AI를 사용해 복약 정보를 추출합니다"""
        
        prompt = f"""
다음 복약 지시사항에서 정보를 추출하여 JSON 형태로 반환해주세요.

복약 지시사항: "{medication_text}"

다음 형태의 JSON으로 응답해주세요:
{{
    "medication_name": "약물명",
    "dosage": "용량 (예: 1정, 5ml)",
    "frequency": "복용 횟수 (1, 2, 3 등의 숫자)",
    "times": ["복용 시간들 (예: 아침, 점심, 저녁, 취침전)"],
    "duration_days": "복용 기간 (일수, 숫자만)",
    "special_instructions": "특별 지시사항"
}}

정보가 명시되지 않았으면 다음 기본값을 사용하세요:
- frequency: 1
- times: ["아침"]
- duration_days: 7
- dosage: "1정"
"""
        
        try:
            model = self.get_model()
            response = model.generate(
                prompt=prompt,
                params={
                    GenParams.MAX_NEW_TOKENS: 200,
                    GenParams.TEMPERATURE: 0.1,
                    GenParams.REPETITION_PENALTY: 1.0
                }
            )
            
            response_text = response['results'][0]['generated_text'].strip()
            print(f"🤖 AI 응답: {response_text}")  # 디버깅용
            
            # JSON 추출 시도
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                print(f"📄 추출된 JSON: {json_str}")  # 디버깅용
                parsed_data = json.loads(json_str)
                print(f"✅ 파싱 성공: {parsed_data}")  # 디버깅용
                return parsed_data
            else:
                raise ValueError("JSON 형태를 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"❌ AI 파싱 실패: {e}")
            # 기본값 반환
            return {
                "medication_name": medication_text[:50] + "..." if len(medication_text) > 50 else medication_text,
                "dosage": "1정",
                "frequency": 1,
                "times": ["아침"],
                "duration_days": 7,
                "special_instructions": "처방전에 따라 복용하세요"
            }
    
    def convert_to_calendar_events(self, medication_info: Dict, start_date: datetime = None) -> List[Dict]:
        """복약 정보를 Google Calendar 이벤트 형태로 변환합니다"""
        
        if not start_date:
            start_date = datetime.now(self.korea_tz).replace(hour=9, minute=0, second=0, microsecond=0)
        elif start_date.tzinfo is None:
            # 타임존이 없으면 한국 시간으로 설정
            start_date = self.korea_tz.localize(start_date)
        
        events = []
        
        # 시간대 매핑
        time_mapping = {
            "아침": 8,
            "점심": 12,
            "저녁": 18,
            "취침전": 21,
            "식전": 7,
            "식후": 13
        }
        
        medication_name = medication_info.get('medication_name', '복용약')
        dosage = medication_info.get('dosage', '1정')
        times = medication_info.get('times', ['아침'])
        duration_days = medication_info.get('duration_days', 7)
        special_instructions = medication_info.get('special_instructions', '')
        
        print(f"🏥 추출된 복약 정보:")
        print(f"   약물명: '{medication_name}'")
        print(f"   용량: '{dosage}'")
        print(f"   복용 횟수: {len(times)}")
        print(f"   복용 시간: {times}")
        print(f"   복용 기간: {duration_days}일")
        
        # 각 복용 시간별로 이벤트 생성
        for time_str in times:
            hour = time_mapping.get(time_str, 9)
            
            # 시작 시간 설정
            event_start = start_date.replace(hour=hour, minute=0)
            event_end = event_start + timedelta(minutes=30)
            
            # 반복 종료일 계산
            until_date = start_date + timedelta(days=duration_days)
            
            event = {
                'summary': f'💊 {medication_name} 복용 ({time_str})',
                'description': f"""
복용약: {medication_name}
용량: {dosage}
복용시간: {time_str}
특별지시사항: {special_instructions}

⚠️ 정확한 복용을 위해 의사나 약사의 지시를 따르세요.
""".strip(),
                'start': {
                    'dateTime': event_start.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'end': {
                    'dateTime': event_end.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'recurrence': [
                    f'RRULE:FREQ=DAILY;UNTIL={until_date.strftime("%Y%m%dT%H%M%SZ")}'
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                        {'method': 'popup', 'minutes': 5},
                    ],
                },
                'colorId': '10'  # 초록색 (건강/의료)
            }
            
            events.append(event)
        
        return events
    
    def process_medication_text(self, medication_text: str, start_date: datetime = None) -> List[Dict]:
        """전체 파이프라인: 텍스트 → 정보 추출 → 캘린더 이벤트 변환"""
        
        try:
            # 1단계: AI로 정보 추출
            medication_info = self.extract_medication_info(medication_text)
            
            # 2단계: 캘린더 이벤트로 변환
            events = self.convert_to_calendar_events(medication_info, start_date)
            
            return events
            
        except Exception as e:
            print(f"복약 정보 처리 실패: {e}")
            # 실패 시 기본 이벤트 반환
            if not start_date:
                start_date = datetime.now(self.korea_tz).replace(hour=9, minute=0, second=0, microsecond=0)
            
            return [{
                'summary': f'💊 복용약 알림',
                'description': f'처방: {medication_text}\n\n의사나 약사의 지시에 따라 복용하세요.',
                'start': {
                    'dateTime': start_date.isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'end': {
                    'dateTime': (start_date + timedelta(minutes=30)).isoformat(),
                    'timeZone': 'Asia/Seoul',
                },
                'recurrence': [
                    f'RRULE:FREQ=DAILY;COUNT=7'
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
                'colorId': '10'
            }]


# 싱글톤 인스턴스
text_to_cal_converter = TextToCalendarConverter()