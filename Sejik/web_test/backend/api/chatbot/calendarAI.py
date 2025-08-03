# api/chatbot/calendarAI.py
from core.config import settings
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

class CalendarAI:
    def __init__(self):
        # core.config의 settings 사용
        self.ibm_cloud_url = settings.WATSONX_API_URL
        self.project_id = settings.WATSONX_PROJECT_ID
        self.api_key = settings.WATSONX_API_KEY
        
        self.creds = {
            "url": self.ibm_cloud_url,
            "apikey": self.api_key
        }
        
        # 모델 인스턴스 준비
        self.model = Model(
            model_id='ibm/granite-3-3-8b-instruct',
            credentials=self.creds,
            project_id=self.project_id
        )
    
    def get_completion(self, prompt: str) -> str:
        """LLM 모델에게 요청을 보내고 응답을 반환하는 함수"""
        try:
            response = self.model.generate(
                prompt=prompt,
                params={
                    GenParams.MAX_NEW_TOKENS: 300,
                    GenParams.TEMPERATURE: 0.7
                }
            )
            return response['results'][0]['generated_text'].strip()
        except Exception as e:
            raise Exception(f"CalendarAI 모델 호출 실패: {str(e)}")
    
    def analyze_medication_schedule(self, user_question: str) -> str:
        """약물 복용 일정을 분석하고 캘린더 추가 제안"""
        
        prompt = f"""당신은 약물 복용 일정 관리 전문 AI입니다.
사용자의 약물 관련 질문을 분석하여 복용 일정을 파악하고, 구글 캘린더 추가를 제안해주세요.

다음과 같이 응답해주세요:

1. 약물 정보 분석:
   - 약물명과 용량
   - 복용 시간 (아침, 점심, 저녁 등)
   - 복용 기간
   - 복용 방법

2. 복용 일정 제안:
   - 구체적인 복용 시간 제안
   - 복용할 총 기간

3. 캘린더 추가 제안:
   "이 약물 복용 일정을 구글 캘린더에 추가해드릴까요?"라고 물어보세요.

약물 복용은 정확성이 중요하므로, 불명확한 정보가 있다면 추가 질문을 하거나 전문의 상담을 권하세요.

사용자 질문: {user_question}

답변:"""

        try:
            ai_response = self.get_completion(prompt)
            return ai_response
            
        except Exception as e:
            raise Exception(f"CalendarAI 응답 생성 실패: {str(e)}")
    
    def check_confirmation(self, user_response: str) -> bool:
        """사용자 확인 응답 체크 (응, 어, 그래, 추가 등)"""
        user_response_lower = user_response.lower().strip()
        confirmation_words = ['응', '어', '그래', '추가', '네', 'yes', 'y', '좋아', '해줘', '부탁']
        
        return any(word in user_response_lower for word in confirmation_words)
    
    def process_calendar_addition(self, original_medication_text: str) -> dict:
        """캘린더 추가 처리 (text_to_cal_json → cal_agent 순서로)"""
        try:
            # 1단계: text_to_cal_json으로 JSON 변환
            from utils.googleCalender.text_to_cal_json import TextToCalendarJSON
            converter = TextToCalendarJSON()
            json_result = converter.convert_to_calendar_json(original_medication_text)
            
            if not json_result.get('success'):
                return {
                    "success": False,
                    "message": "약물 정보를 캘린더 형식으로 변환할 수 없습니다.",
                    "error": json_result.get('error', 'Unknown error')
                }
            
            # 2단계: cal_agent로 실제 캘린더에 추가
            from utils.googleCalender.cal_agent import CalendarAddAgent
            agent = CalendarAddAgent()
            calendar_result = agent.add_medication_schedule(json_result['google_events'])
            
            return {
                "success": calendar_result['success'],
                "message": calendar_result.get('message', '캘린더 추가 완료'),
                "added_count": calendar_result.get('added_count', 0),
                "details": calendar_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"캘린더 추가 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }

# 테스트
if __name__ == "__main__":
    try:
        calendar_ai = CalendarAI()
        
        test_questions = [
            "타이레놀 500mg을 하루 3번 아침점심저녁으로 3일간 먹어야 해",
            "오메프라졸 20mg 아침 식전에 2주간 복용",
            "아스피린 100mg 매일 저녁 식후에 먹으라고 했는데"
        ]
        
        for question in test_questions:
            print(f"질문: {question}")
            result = calendar_ai.analyze_medication_schedule(question)
            print(f"답변: {result}")
            print("-" * 80)
    except Exception as e:
        print(f"오류: {e}")
