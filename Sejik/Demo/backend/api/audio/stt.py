# from fastapi import APIRouter, UploadFile, File
# from core.config import settings
# import requests

# router = APIRouter()

# @router.post("/audio/stt")
# async def stt_recognize(file: UploadFile = File(...)):
#     model = "ko-KR_BroadbandModel"
#     stt_url = f"{settings.WATSON_STT_URL}/v1/recognize?model={model}"

#     headers = {
#         "Content-Type": "audio/webm",
#         "Accept": "application/json"
#     }

#     audio_bytes = await file.read()

#     response = requests.post(
#         stt_url,
#         headers=headers,
#         data=audio_bytes,
#         auth=("apikey", settings.WATSON_STT_API_KEY)
#     )

#     if response.status_code != 200:
#         return {"error": f"STT 실패: {response.status_code}, {response.text}"}

#     results = response.json().get("results", [])
#     if not results:
#         return {"text": ""}

#     transcript = results[0]["alternatives"][0]["transcript"]
#     return {"text": transcript}


#google TTS 예제

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import os
from schemas.chat import ChatRequest, ChatResponse
from google.cloud import speech

router = APIRouter()

@router.post("/audio/stt")
async def stt_recognize(file: UploadFile = File(...)):
    # [환경변수 등록]
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
        os.path.dirname(__file__), "gen-lang-client.json"
    )

    # Google Speech-to-Text client
    client = speech.SpeechClient()

    audio_bytes = await file.read()

    # Google STT는 여러 AudioEncoding 지원, webm(Opus) 등 대부분 자동 인식 가능
    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # webm이면 WEBM_OPUS, wav면 LINEAR16
        language_code="ko-KR",   # 한국어
        sample_rate_hertz=48000,  # 샘플레이트(대부분 webm/MediaRecorder면 48000, wav면 적당히 맞춤)
        audio_channel_count=1,    # 모노/스테레오 등 (일반적으로 1)
        enable_automatic_punctuation=True,  # 자동 구두점 부여
    )

    try:
        response = client.recognize(config=config, audio=audio)
        if not response.results:
            return {"text": ""}
        transcript = response.results[0].alternatives[0].transcript

        #transcript = (f"{transcript} " f"사용자의 기저질환(참고용): {request.underlying_diseases} "f"현재 복용 중인 약물(참고용): {request.current_medications}")

        return {"text": transcript}
    except Exception as e:
        return {"error": str(e)}
