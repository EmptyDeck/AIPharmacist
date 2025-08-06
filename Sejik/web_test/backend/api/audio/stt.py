from fastapi import APIRouter, UploadFile, File
from core.config import settings
import requests

router = APIRouter()

@router.post("/audio/stt")
async def stt_recognize(file: UploadFile = File(...)):
    model = "ko-KR_BroadbandModel"
    stt_url = f"{settings.STT_URL}/v1/recognize?model={model}"

    headers = {
        "Content-Type": "audio/webm",
        "Accept": "application/json"
    }

    audio_bytes = await file.read()

    response = requests.post(
        stt_url,
        headers=headers,
        data=audio_bytes,
        auth=("apikey", settings.STT_API_KEY)
    )

    if response.status_code != 200:
        return {"error": f"STT 실패: {response.status_code}, {response.text}"}

    results = response.json().get("results", [])
    if not results:
        return {"text": ""}

    transcript = results[0]["alternatives"][0]["transcript"]
    return {"text": transcript}
