import requests
from core.config import settings

class WarnAI:
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
    
    def get_drug_warnings(self, user_question: str) -> str:
        """약물의 부작용 및 주의사항 정보 제공"""

        user_prompt = f"약물 안전성 질문: {user_question}"
        
        payload = {
            "messages": [
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
            return result.get('choices', [{}])[0].get('message', {}).get('content', '응답을 생성할 수 없습니다.')
            
        except Exception as e:
            raise Exception(f"WarnAI 응답 생성 실패: {str(e)}")

# 테스트
if __name__ == "__main__":
    try:
        warn_ai = WarnAI()
        
        test_questions = [
            "타이레놀의 부작용이 뭐야?",
            "아스피린을 먹으면 위험한가요?",
            "이부프로펜 주의사항 알려주세요"
        ]
        
        for question in test_questions:
            response = warn_ai.get_drug_warnings(question)
            print(f"질문: {question}")
            print(f"답변: {response}")
            print("-" * 80)
    except Exception as e:
        print(f"오류: {e}")
