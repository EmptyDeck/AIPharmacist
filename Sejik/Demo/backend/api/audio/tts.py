# Watson TTS 예제
# from fastapi import APIRouter
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from core.config import settings
# import requests
# import uuid
# import os

# import traceback

# router = APIRouter()

# class TextInput(BaseModel):
#     text: str

# @router.post("/audio/tts")
# def tts_synthesize(data: TextInput):
#     print("[TTS] 요청 text:", data.text)

#     voice = "ko-KR_JinV3Voice"
#     tts_url = f"{settings.WATSON_TTS_URL}/v1/synthesize?voice={voice}"
#     print("[TTS] 요청 url:", tts_url)

#     headers = {
#         "Content-Type": "application/json",
#         "Accept": "audio/webm"
#     }
#     payload = {"text": data.text}

#     try:
#         print("[TTS] IBM TTS API 요청 시작...")
#         response = requests.post(
#             tts_url,
#             headers=headers,
#             json=payload,
#             auth=("apikey", settings.WATSON_TTS_API_KEY),
#             timeout=10
#         )
#         print("[TTS] IBM 응답 status_code:", response.status_code)
#         print("[TTS] IBM 응답 Headers:", response.headers)
#         # 만약 오디오가 아니면 일부 데이터 프린트
#         if response.status_code != 200 or not response.headers.get("content-type", "").startswith("audio"):
#             print("[TTS] 응답 내용(일부):", response.text[:300])
#     except Exception as e:
#         print("[TTS] IBM 요청 Exception 발생:", e)
#         traceback.print_exc()
#         return {"error": str(e)}

#     if response.status_code != 200:
#         # IBM 응답이 text/html, application/json이면 그 내용 로그
#         # (예: 키오류, 요금, 일일제한, 인증오류, quota 등)
#         return {"error": f"TTS 실패: {response.status_code}, {response.text}"}

#     # 경로지정 부분(이미 올바름)
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     save_dir = os.path.join(current_dir, "temp")
#     os.makedirs(save_dir, exist_ok=True)
#     filename = f"output_{uuid.uuid4().hex}.webm"
#     output_path = os.path.join(save_dir, filename)
#     print("[TTS] 파일 저장 경로:", output_path)
#     print("[TTS] 응답 content-type:", response.headers.get("content-type"))
#     print("[TTS] 응답 content-length:", response.headers.get("content-length"))

#     # 혹시 오디오 데이터가 너무 작을 경우 경고
#     if len(response.content) < 5000:  # 파일이 5KB 이하면 이상할 수 있음
#         print("[TTS] [경고] 오디오 크기가 비정상적으로 작다!", len(response.content))

#     with open(output_path, "wb") as f:
#         f.write(response.content)
#     print("[TTS] 파일 저장 완료")

#     return FileResponse(output_path, media_type="audio/webm", filename=filename)




# 구글 API를 사용한 TTS 예제
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.cloud import texttospeech
import uuid
import os

router = APIRouter()

class TextInput(BaseModel):
    text: str

@router.post("/audio/tts")
def tts_synthesize(data: TextInput):
    # 서비스계정 인증 경로 지정
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(__file__), "gen-lang-client.json")

    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=data.text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Chirp3-HD-Fenrir",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(current_dir, "temp")
    os.makedirs(save_dir, exist_ok=True)
    filename = f"output_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(save_dir, filename)

    with open(output_path, "wb") as out:
        out.write(response.audio_content)

    return FileResponse(output_path, media_type="audio/mp3", filename=filename)

