import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from core.config import settings

router = APIRouter()

# 모델 인증 정보 및 초기화
creds = {
    "url": settings.IBM_CLOUD_URL,
    "apikey": settings.API_KEY
}

try:
    model = Model(
        model_id='ibm/granite-3-3-8b-instruct',
        credentials=creds,
        project_id=settings.PROJECT_ID
    )
except Exception as e:
    logging.error(f"🛑 IBM 모델 초기화 실패: {e}")
    raise e

def get_completion(prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
    try:
        response = model.generate(
            prompt=prompt,
            params={
                GenParams.MAX_NEW_TOKENS: 100,
                GenParams.TEMPERATURE: temperature
            }
        )
        return response['results'][0]['generated_text']
    except Exception as e:
        logging.error(f"🛑 GPT 응답 오류: {e}")
        return "⚠️ GPT 응답에 실패했습니다."

class GPTRequest(BaseModel):
    message: str

@router.post("/audio/gpt")
async def gpt_response(request: GPTRequest):
    prompt = f"""
    당신은 '닥터왓슨'이라는 사람의 약국 의사입니다. 다음 메세지에 대해서 답변을 작성해주세요.
    그리고 답변은 3문장 이내로 작성해주세요.
    사용자의 입력은 이상할 수 있습니다. 현재 사용자는 STT를 이용하기 때문에 만약 사용자의 입력이 이상하다면 눈치로 이해해주세요.
    ``````
    """
    response_text = get_completion(prompt)
    return {"text": response_text}



# 에이전트 코드(성능 향상 해야함)
# import requests
# import logging
# from fastapi import APIRouter
# from pydantic import BaseModel
# from core.config import settings

# router = APIRouter()

# class GPTRequest(BaseModel):
#     message: str

# @router.post("/audio/gpt")
# async def gpt_response(request: GPTRequest):
#     print("GPT 요청 수신:", request.message)
    
#     response_text = get_completion(request.message)
#     return {"text": response_text}

# def get_completion(user_message: str) -> str:
#     try:
#         # 토큰 획득
#         token_response = requests.post('https://iam.cloud.ibm.com/identity/token', 
#                                     data={"apikey": settings.API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
#         mltoken = token_response.json()["access_token"]
        
#         # 헤더 설정
#         header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}
        
#         # 페이로드 - 코드 2와 동일한 구조
#         payload_scoring = {
#             "messages": [
#                 {"role": "user", "content": user_message}
#             ]
#         }
        
#         # API 호출
#         response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/a13f7396-1142-40d6-9531-f7719be5f3fe/ai_service?version=2021-05-01', 
#                                        json=payload_scoring, headers=header)
        
#         # 응답 확인 (코드 2처럼)
#         #print("Scoring response")
#         try:
#             response_data = response_scoring.json()
#             print(response_data)
#             # choices가 있으면 파싱, 없으면 전체 응답 반환
#             if 'choices' in response_data:
#                 return response_data['choices'][0]['message']['content']
#             else:
#                 # 다른 형식의 응답일 경우 전체 응답을 문자열로 반환
#                 return str(response_data)
#         except ValueError:
#             print(response_scoring.text)
#             return response_scoring.text
        
#     except Exception as e:
#         logging.error(f"🛑 GPT 응답 오류: {e}")
#         return "⚠️ GPT 응답에 실패했습니다."