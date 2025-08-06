from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from core.config import settings
import requests
import uuid
import os

router = APIRouter()

class TextInput(BaseModel):
    text: str

@router.post("/audio/tts")
def tts_synthesize(data: TextInput):
    voice = "ko-KR_JinV3Voice"
    tts_url = f"{settings.TTS_URL}/v1/synthesize?voice={voice}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/webm"
    }

    payload = {"text": data.text}

    response = requests.post(
        tts_url,
        headers=headers,
        json=payload,
        auth=("apikey", settings.TTS_API_KEY)
    )

    if response.status_code != 200:
        return {"error": f"TTS 실패: {response.status_code}, {response.text}"}

    filename = f"output_{uuid.uuid4().hex}.webm"
    output_path = os.path.join("00temp_back/voice_tmp", filename)

    with open(output_path, "wb") as f:
        f.write(response.content)

    return FileResponse(output_path, media_type="audio/webm", filename=filename)
