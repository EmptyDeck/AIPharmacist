# import logging
# from typing import Optional

# from fastapi import APIRouter
# from pydantic import BaseModel
# from ibm_watson_machine_learning.foundation_models import Model
# from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
# from core.config import settings

# router = APIRouter()

# # 모델 인증 정보 및 초기화
# creds = {
#     "url": settings.WATSONX_API_URL,
#     "apikey": settings.WATSONX_API_KEY
# }

# try:
#     model = Model(
#         model_id='ibm/granite-3-3-8b-instruct',
#         credentials=creds,
#         project_id=settings.WATSONX_PROJECT_ID
#     )
# except Exception as e:
#     logging.error(f"🛑 IBM 모델 초기화 실패: {e}")
#     raise e

# def get_completion(prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
#     try:
#         response = model.generate(
#             prompt=prompt,
#             params={
#                 GenParams.MAX_NEW_TOKENS: 100,
#                 GenParams.TEMPERATURE: temperature
#             }
#         )
#         return response['results'][0]['generated_text']
#     except Exception as e:
#         logging.error(f"🛑 GPT 응답 오류: {e}")
#         return "⚠️ GPT 응답에 실패했습니다."

# class GPTRequest(BaseModel):
#     message: str

# @router.post("/audio/gpt")
# async def gpt_response(request: GPTRequest):
#     prompt = f"""
#     당신은 '닥터왓슨'이라는 사람의 약국 의사입니다. 다음 메세지에 대해서 답변을 작성해주세요.
#     그리고 답변은 3문장 이내로 작성해주세요.
#     사용자의 입력은 이상할 수 있습니다. 현재 사용자는 STT를 이용하기 때문에 만약 사용자의 입력이 이상하다면 눈치로 이해해주세요.
#     ``````
#     """
#     response_text = get_completion(prompt)
#     return {"text": response_text}


# #backend/api/audio/gpt.py
# import logging
# import os
# from typing import Optional

# from fastapi import APIRouter
# from pydantic import BaseModel
# from core.config import settings

# # Gemini Python SDK import
# from google import genai

# router = APIRouter()

# # GEMINI_API_KEY를 환경변수에 등록
# os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

# # Gemini client 객체 생성 (환경변수 자동 인식)
# client = genai.Client()

# def get_completion(prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash-001",
#             contents=prompt
#         )

#         return response.text
#     except Exception as e:
#         logging.error(f"🛑 gpt.py 응답 오류: {e}")
#         return "⚠️ gpt.py 응답에 실패했습니다."


# class GPTRequest(BaseModel):
#     message: str

# @router.post("/audio/gpt")
# async def gpt_response(request: GPTRequest):
#     prompt = (
#         "너는 이름이 '닥터왓슨'인 한국인 약사 챗봇이야"
#         "자연스럽고 친근한 구어체로 짧게 대답해줘"
#         "최대 2문장 이내, 절대 목록·나열·장문 피해"
#         "상대가 음성으로 말하듯 물어보면, 그것을 듣고 일상대화하듯 답변해줘. "
#         "어떤 주제든 약국 약사 톤을 벗어나지 말고, 사용자의 입력이 어색하거나 불분명해도, 맥락상 가장 좋은 안내를 잠깐(최대 2문장) 해줘. "
#         "반드시 존댓말을 유지해줘"
#         "사용자는 STT를 이용하기 때문에 만약 사용자의 입력이 이상하다면 최대한 잘 예측해줘." \
#         "콤마 사용하지 말고, 사용해야하면 꼭 띄어쓰기로 해줘"
#         "이모티콘 적지마"
#         f"{request.message}"
#     )
#     response_text = get_completion(prompt)
#     return {"text": response_text}


# + cal

# backend/api/audio/gpt.py
import logging
import os
import asyncio
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.config import settings

# Google-Gemini SDK
from google import genai

# 캘린더용 AI & 에이전트
from api.chatbot.calendarAI import calendar_ai       # 분석·추가 담당

router = APIRouter()

# ───────────────────────────────────────
# Gemini 초기화 (코드2와 동일)
# ───────────────────────────────────────
os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
client = genai.Client()
MODEL_ID = "gemini-2.0-flash-001"


def gemini_completion(prompt: str) -> str:
    try:
        resp = client.models.generate_content(model=MODEL_ID, contents=prompt)
        return resp.text.strip()
    except Exception as e:
        logging.error(f"🛑 Gemini 호출 오류: {e}")
        raise HTTPException(status_code=500, detail="Gemini 호출 실패")


# ───────────────────────────────────────
#  사용자 세션 (캘린더 확인용)
# ───────────────────────────────────────
# key = speaker_id (지금은 'voice_user' 고정)
_user_sessions: Dict[str, Dict] = {}


class VoiceRequest(BaseModel):
    message: str
    speaker_id: str | None = None   # 필요하면 모바일 UUID 등


# ───────────────────────────────────────
#  메인 라우터
# ───────────────────────────────────────
@router.post("/audio/gpt")
async def voice_chat(req: VoiceRequest):

    user_id = req.speaker_id or "voice_user"     # 간단히 고정

    # ① 이미 '추가할까요?' 질문 뒤 응답 단계인지?
    if user_id in _user_sessions and _user_sessions[user_id]["waiting_confirm"]:
        if calendar_ai.check_confirmation(req.message):
            # 긍정 → 캘린더 실제 추가
            original = _user_sessions[user_id]["original_text"]
            result = await asyncio.get_event_loop().run_in_executor(
                None, calendar_ai.process_calendar_addition, original
            )

            del _user_sessions[user_id]          # 세션 정리

            if result.get("success"):
                return {"text": "캘린더에 성공적으로 등록했어요."}
            return {"text": "일정을 추가하지 못했어요. 잠시 후 다시 시도해 주세요."}

        else:
            # 부정 또는 기타 → 취소
            del _user_sessions[user_id]
            return {"text": "네 알겠습니다. 캘린더에는 추가하지 않을게요."}

    # ---------------------------------------------
    # ② 복약 일정 의도 감지 → ‘요약+질문’ 단계
    # ---------------------------------------------
    lowered = req.message.lower()
    drug_keywords = ["캘린더", "일정", "알람", "구글"]

    # drug 키워드가 하나라도 있고 아직 확인 세션이 없으면 → 일정 분석
    if any(k in lowered for k in drug_keywords) and user_id not in _user_sessions:
        # 1) (이벤트 생성용) CalendarAI 내부 분석 호출  ─ 삭제해도 무방
        await asyncio.get_event_loop().run_in_executor(
            None, calendar_ai.analyze_medication_schedule, req.message
        )

        # 2) 음성용 ‘요약 + 등록 여부’ 문장 Gemini로 생성
        summary_prompt = (
            "너는 한국인 약사 챗봇이다. 사용자의 복약 지시를 한 문장으로 요약한 뒤 "
            "마지막에 ‘이 일정을 구글 캘린더에 등록해 드릴까요?’ 를 붙여라. "
            "만약, '약이름, 복용시간, 몇일간 먹는지가 명확하지 않다면, 명확히 알려달라고 요청할것"
            "존댓말 구어체, 120자 이하, 목록·특수기호·이모티콘 금지.\n\n"
            f"복약 지시: {req.message}"
        )
        voice_answer = gemini_completion(summary_prompt)

        # 3) 세션 저장 → 다음 턴에서 Yes/No 판별
        _user_sessions[user_id] = {
            "waiting_confirm": True,
            "original_text":   req.message
        }
        return {"text": voice_answer}   # 길이 제한

    # ③ 일반 대화 → Gemini 짧은 답
    prompt = (
        "너는 이름이 '닥터왓슨'인 한국인 약사 챗봇이야"
        "너는 복약 상담과 약에대한 궁금증을 해결할수 있고, 약에 대한 일정을 캘린더에 추가할 수 있어"
        "자연스럽고 친근한 구어체로 짧게 대답해줘"
        "최대 2문장 이내, 절대 목록·나열·장문 피해"
        "상대가 음성으로 말하듯 물어보면, 그것을 듣고 일상대화하듯 답변해줘. "
        "어떤 주제든 약국 약사 톤을 벗어나지 말고, 사용자의 입력이 어색하거나 불분명해도, 맥락상 가장 좋은 안내를 잠깐(최대 2문장) 해줘. "
        "반드시 존댓말을 유지해줘"
        "사용자는 STT를 이용하기 때문에 만약 사용자의 입력이 이상하다면 최대한 잘 예측해줘."
        "콤마 사용하지 말고, 사용해야하면 꼭 띄어쓰기로 해줘"
        "이모티콘,특수기호 쓰지마"
        f"{req.message}"
    )
    answer = gemini_completion(prompt)
    return {"text": answer}
