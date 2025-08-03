import requests
from core.config import settings

class ExplainAI:
    def __init__(self):
        # core.config의 settings 사용 (환경변수 이름 맞춤)
        self.api_key = settings.WATSONX_API_KEY  # API_KEY -> WATSONX_API_KEY
        self.endpoint = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/6261f83b-14d4-4666-9243-2cb36bdcd698/ai_service?version=2021-05-01"
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
    
    def explain_drug(self, user_question: str) -> str:
        """약물에 대한 상세한 설명 제공"""
        
        system_prompt = """당신은 전문적인 약물 정보 설명 AI입니다. 
사용자의 약물 관련 질문에 대해 정확하고 이해하기 쉬운 설명을 제공해주세요.

다음 사항들을 포함하여 설명해주세요:
- 약물의 주요 효능과 작용 원리
- 주요 성분과 그 역할
- 일반적인 복용법과 용량
- 복용 시 주의사항
- 다른 약물과의 상호작용 (있는 경우)

항상 정확한 정보를 제공하되, 개인차가 있을 수 있음을 명시하고
구체적인 복용 지침은 전문의나 약사와 상담할 것을 권해주세요."""

        user_prompt = f"약물 설명 요청: {user_question}"
        
        payload = {
            "messages": [
                {"content": system_prompt, "role": "system"},
                {"content": user_prompt, "role": "user"}
            ]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '설명을 생성할 수 없습니다.')
            
        except Exception as e:
            raise Exception(f"ExplainAI 응답 생성 실패: {str(e)}")

# 테스트
if __name__ == "__main__":
    try:
        explain_ai = ExplainAI()
        
        test_questions = [
            "아스피린의 효능이 뭐예요?",
            "타이레놀의 성분과 작용원리를 알려주세요",
            "이부프로펜은 어떤 약인가요?"
        ]
        
        for question in test_questions:
            response = explain_ai.explain_drug(question)
            print(f"질문: {question}")
            print(f"답변: {response}")
            print("-" * 80)
    except Exception as e:
        print(f"오류: {e}")
