# Sejik/Demo/backend/api/chatbot/explainAI.py
import requests
from core.config import settings


class ExplainAI:
    def __init__(self):
        self.api_key = settings.WATSONX_API_KEY
        self.endpoint = (
            "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/"
            "cd48d1c5-428f-47d9-a17d-710a60d340a7/ai_service?version=2021-05-01"
        )
        self.token = self._get_token()

    def _get_token(self) -> str:
        res = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "apikey": self.api_key,
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            },
            timeout=30,
        )
        res.raise_for_status()
        return res.json()["access_token"]

    def explain_drug(self, user_question: str) -> str:
        """약물 설명 생성"""
        user_prompt = f"약물 설명 요청: {user_question}"   # ✅ set → str

        payload = {
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        try:
            resp = requests.post(self.endpoint, json=payload,
                                 headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "설명을 생성할 수 없습니다.")
            )
        except Exception as e:
            raise Exception(f"ExplainAI 응답 생성 실패: {e}")


# 간단 테스트
if __name__ == "__main__":
    ai = ExplainAI()
    print(ai.explain_drug("아스피린의 효능이 뭐예요?"))
