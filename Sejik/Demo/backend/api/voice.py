# import os
# import tempfile
# import httpx
# import base64
# try:
#     import magic
#     MAGIC_AVAILABLE = True
# except ImportError:
#     MAGIC_AVAILABLE = False
#     print("Warning: python-magic not available. File type detection will use filename extensions.")

# from fastapi import APIRouter, HTTPException, UploadFile, File, Form
# from fastapi.responses import FileResponse, StreamingResponse
# from typing import Optional, Dict, Any
# import io
# import asyncio
# from concurrent.futures import ThreadPoolExecutor

# # IBM Watson imports
# from ibm_watson import SpeechToTextV1, TextToSpeechV1
# from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
# from ibm_watson.websocket import RecognizeCallback, AudioSource

# # Audio processing
# from pydub import AudioSegment
# from pydub.exceptions import CouldntDecodeError

# # Configuration
# from core.config import settings
# from api.chat import get_chat_response
# from schemas.chat import ChatRequest

# # APIRouter 인스턴스 생성
# router = APIRouter()

# # IBM Watson 서비스 인스턴스 (Singleton 패턴)
# _stt_service: Optional[SpeechToTextV1] = None
# _tts_service: Optional[TextToSpeechV1] = None


# def get_stt_service() -> SpeechToTextV1:
#     """IBM Watson Speech-to-Text 서비스 인스턴스를 반환합니다"""
#     global _stt_service
#     if _stt_service is None:
#         if not settings.WATSON_STT_API_KEY:
#             raise HTTPException(
#                 status_code=500,
#                 detail="IBM Watson STT API 키가 설정되지 않았습니다."
#             )
        
#         authenticator = IAMAuthenticator(settings.WATSON_STT_API_KEY)
#         _stt_service = SpeechToTextV1(authenticator=authenticator)
#         _stt_service.set_service_url(settings.WATSON_STT_URL)
    
#     return _stt_service


# def get_tts_service() -> TextToSpeechV1:
#     """IBM Watson Text-to-Speech 서비스 인스턴스를 반환합니다"""
#     global _tts_service
#     if _tts_service is None:
#         if not settings.WATSON_TTS_API_KEY:
#             raise HTTPException(
#                 status_code=500,
#                 detail="IBM Watson TTS API 키가 설정되지 않았습니다."
#             )
        
#         authenticator = IAMAuthenticator(settings.WATSON_TTS_API_KEY)
#         _tts_service = TextToSpeechV1(authenticator=authenticator)
#         _tts_service.set_service_url(settings.WATSON_TTS_URL)
    
#     return _tts_service


# def validate_audio_file(file_content: bytes, max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
#     """오디오 파일을 검증하고 메타데이터를 반환합니다"""
#     if len(file_content) > max_size:
#         raise HTTPException(
#             status_code=413,
#             detail=f"파일 크기가 너무 큽니다. 최대 {max_size // 1024 // 1024}MB까지 지원합니다."
#         )
    
#     if len(file_content) < 1024:  # 1KB 미만
#         raise HTTPException(
#             status_code=400,
#             detail="오디오 파일이 너무 작습니다."
#         )
    
#     # MIME 타입 검증 (magic이 없을 때는 간단한 확장자 검사)
#     if MAGIC_AVAILABLE:
#         file_type = magic.from_buffer(file_content, mime=True)
#         supported_types = [
#             'audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/ogg',
#             'audio/webm', 'audio/x-wav', 'audio/flac'
#         ]
        
#         if file_type not in supported_types:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"지원하지 않는 오디오 형식입니다. 지원 형식: {', '.join(supported_types)}"
#             )
#     else:
#         # Fallback: 파일 헤더로 간단 검증
#         if file_content[:4] == b'RIFF' and file_content[8:12] == b'WAVE':
#             file_type = 'audio/wav'
#         elif file_content[:3] == b'ID3' or file_content[:2] == b'\xff\xfb':
#             file_type = 'audio/mpeg'
#         elif file_content[:4] == b'OggS':
#             file_type = 'audio/ogg'
#         else:
#             file_type = 'audio/unknown'  # 일단 통과시키고 pydub에서 처리하도록
    
#     return {
#         "file_type": file_type,
#         "file_size": len(file_content),
#         "is_valid": True
#     }


# def convert_audio_format(file_content: bytes, target_format: str = "wav") -> bytes:
#     """오디오 파일을 지정된 형식으로 변환합니다"""
#     try:
#         # BytesIO로 메모리에서 처리
#         audio_io = io.BytesIO(file_content)
        
#         # FFmpeg가 없는 Windows 환경에서는 변환 없이 원본 반환
#         try:
#             audio = AudioSegment.from_file(audio_io)
            
#             # WAV 형식으로 변환 (16kHz, mono)
#             audio = audio.set_frame_rate(16000).set_channels(1)
            
#             output_io = io.BytesIO()
#             audio.export(output_io, format=target_format)
#             output_io.seek(0)
            
#             return output_io.getvalue()
#         except Exception as ffmpeg_error:
#             print(f"FFmpeg 변환 실패, 원본 파일 사용: {ffmpeg_error}")
#             # FFmpeg가 없으면 원본 파일 그대로 사용 (Watson이 대부분 형식 지원)
#             return file_content
            
#     except CouldntDecodeError:
#         raise HTTPException(
#             status_code=400,
#             detail="오디오 파일을 디코딩할 수 없습니다."
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"오디오 변환 중 오류가 발생했습니다: {str(e)}"
#         )


# @router.post("/voice/stt", summary="음성을 텍스트로 변환")
# async def speech_to_text(
#     audio_file: UploadFile = File(..., description="변환할 오디오 파일"),
#     model: str = Form(default="ko-KR_BroadbandModel", description="사용할 STT 모델"),
#     confidence_threshold: float = Form(default=0.5, description="신뢰도 임계값")
# ):
#     """
#     업로드된 오디오 파일을 텍스트로 변환합니다.
    
#     - **audio_file**: 음성 파일 (WAV, MP3, MP4, OGG, WebM, FLAC 지원)
#     - **model**: IBM Watson STT 모델 (기본: 한국어 광대역 모델)
#     - **confidence_threshold**: 결과 신뢰도 최소 임계값
#     """
#     try:
#         # 파일 읽기
#         file_content = await audio_file.read()
        
#         # 파일 검증
#         validation_result = validate_audio_file(file_content)
        
#         # 원본 파일의 MIME 타입 감지
#         original_type = validation_result.get('file_type', 'audio/unknown')
        
#         # Watson이 지원하는 content-type으로 매핑
#         content_type_mapping = {
#             'audio/wav': 'audio/wav',
#             'audio/x-wav': 'audio/wav', 
#             'audio/mpeg': 'audio/mp3',
#             'audio/mp4': 'audio/mp4',
#             'audio/ogg': 'audio/ogg',
#             'audio/webm': 'audio/webm',
#             'audio/flac': 'audio/flac',
#             'audio/unknown': 'audio/wav'  # 기본값
#         }
        
#         watson_content_type = content_type_mapping.get(original_type, 'audio/wav')
        
#         # REST API 직접 호출로 STT 처리 (노트북 방식)
#         def direct_stt_call():
#             # Watson STT REST API 엔드포인트 (model을 URL 파라미터로)
#             stt_url = f"{settings.WATSON_STT_URL}/v1/recognize?model={model}"
            
#             headers = {
#                 'Content-Type': watson_content_type,
#                 'Accept': 'application/json'
#             }
            
#             with httpx.Client(timeout=60.0) as client:
#                 response = client.post(
#                     stt_url, 
#                     headers=headers,
#                     content=file_content,  # 바이너리 오디오 데이터
#                     auth=('apikey', settings.WATSON_STT_API_KEY)  # 노트북과 동일한 인증
#                 )
#             response.raise_for_status()
            
#             return response.json()
        
#         # 음성 인식 실행
#         loop = asyncio.get_event_loop()
#         recognition_result = await loop.run_in_executor(None, direct_stt_call)
        
#         # 결과 처리
#         if not recognition_result.get('results'):
#             return {
#                 "text": "",
#                 "confidence": 0.0,
#                 "message": "음성을 인식할 수 없습니다.",
#                 "status": "no_speech"
#             }
        
#         # 가장 신뢰도가 높은 결과 선택
#         best_result = recognition_result['results'][0]
#         if not best_result.get('alternatives'):
#             return {
#                 "text": "",
#                 "confidence": 0.0,
#                 "message": "대안 결과가 없습니다.",
#                 "status": "no_alternatives"
#             }
        
#         best_alternative = best_result['alternatives'][0]
#         confidence = best_alternative.get('confidence', 0.0)
#         transcript = best_alternative.get('transcript', '').strip()
        
#         # 신뢰도 검증
#         if confidence < confidence_threshold:
#             return {
#                 "text": transcript,
#                 "confidence": confidence,
#                 "message": f"음성 인식 신뢰도가 낮습니다 ({confidence:.2f} < {confidence_threshold})",
#                 "status": "low_confidence"
#             }
        
#         return {
#             "text": transcript,
#             "confidence": confidence,
#             "message": "음성 인식 성공",
#             "status": "success",
#             "metadata": {
#                 "model_used": model,
#                 "file_info": validation_result,
#                 "alternatives_count": len(best_result['alternatives']),
#                 "word_count": len(transcript.split())
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"음성 인식 중 오류가 발생했습니다: {str(e)}"
#         )


# @router.post("/voice/tts", summary="텍스트를 음성으로 변환")
# async def text_to_speech(
#     text: str = Form(..., description="음성으로 변환할 텍스트"),
#     voice: str = Form(default="ko-KR_HyunjunVoice", description="사용할 TTS 음성"),
#     audio_format: str = Form(default="mp3", description="출력 오디오 형식")
# ):
#     """
#     텍스트를 음성으로 변환하여 오디오 파일을 반환합니다.
    
#     - **text**: 음성으로 변환할 텍스트
#     - **voice**: IBM Watson TTS 음성 (기본: 한국어 Jin 음성)
#     - **audio_format**: 출력 형식 (mp3, wav, flac, ogg)
#     """
#     try:
#         if not text.strip():
#             raise HTTPException(
#                 status_code=400,
#                 detail="변환할 텍스트를 입력해주세요."
#             )
        
#         if len(text) > 5000:  # 텍스트 길이 제한
#             raise HTTPException(
#                 status_code=400,
#                 detail="텍스트가 너무 깁니다. 5000자 이하로 입력해주세요."
#             )
        
#         # 지원 형식 검증
#         supported_formats = ["mp3", "wav", "flac", "ogg"]
#         if audio_format not in supported_formats:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"지원하지 않는 오디오 형식입니다. 지원 형식: {', '.join(supported_formats)}"
#             )
        
#         # 음성 합성 실행
#         loop = asyncio.get_event_loop()
        
#         # REST API 직접 호출로 UTF-8 인코딩 문제 해결
#         def direct_tts_call():
#             # 이모지 및 특수문자 제거 (TTS 호환성을 위해)
#             import re
            
#             # 완전한 ASCII 호환 텍스트 생성 (Latin-1 문제 완전 해결)
#             def make_tts_safe_text(text):
#                 import unicodedata
#                 import re
                
#                 # 1. 모든 이모지와 특수문자 완전 제거
#                 cleaned = ''.join(char for char in text if unicodedata.category(char) not in ['So', 'Sk', 'Sm', 'Cn'])
                
#                 # 2. 마크다운 제거
#                 cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
#                 cleaned = re.sub(r'\n+', ' ', cleaned)
#                 cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
#                 # 3. Latin-1로 인코딩 불가능한 모든 문자 찾아서 제거
#                 safe_chars = []
#                 for char in cleaned:
#                     try:
#                         char.encode('latin-1')
#                         safe_chars.append(char)
#                     except UnicodeEncodeError:
#                         # Latin-1로 인코딩 불가능한 문자는 공백으로 대체
#                         safe_chars.append(' ')
                
#                 # 4. 연속된 공백 정리
#                 final_text = ''.join(safe_chars)
#                 final_text = re.sub(r'\s+', ' ', final_text).strip()
                
#                 return final_text
            
#             # 텍스트 정리 (Latin-1 완전 호환)
#             cleaned_text = make_tts_safe_text(text)  # 완전한 ASCII 호환 변환
            
#             # Watson TTS REST API 엔드포인트 (voice는 URL 파라미터로)
#             tts_url = f"{settings.WATSON_TTS_URL}/v1/synthesize?voice={voice}"
            
#             # Basic 인증 헤더 생성
#             auth_string = f"apikey:{settings.WATSON_TTS_API_KEY}"
#             auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
            
#             headers = {
#                 'Content-Type': 'application/json; charset=utf-8',  # UTF-8 명시
#                 'Accept': f'audio/{audio_format}',
#                 'Authorization': f'Basic {auth_b64}'
#             }
            
#             data = {
#                 'text': cleaned_text,  # 정리된 텍스트 사용
#                 'voice': voice
#             }
            
#             # HTTPX를 사용한 완전한 UTF-8 제어
#             import json
#             import httpx
            
#             # 완벽한 UTF-8 JSON 직렬화
#             json_data = json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'))
#             json_bytes = json_data.encode('utf-8')
            
#             # HTTPX용 헤더 설정 (Authorization은 auth 파라미터로)
#             headers_httpx = {
#                 'Content-Type': 'application/json; charset=utf-8',
#                 'Accept': f'audio/{audio_format}',
#                 'Content-Length': str(len(json_bytes))
#             }
            
#             print(f"🔍 TTS 디버그: HTTPX로 UTF-8 바이트 {len(json_bytes)}개 전송")
            
#             with httpx.Client(timeout=30.0) as client:
#                 response = client.post(
#                     tts_url,
#                     headers=headers_httpx,
#                     content=json_bytes,  # 완전한 UTF-8 바이트 제어
#                     auth=('apikey', settings.WATSON_TTS_API_KEY)  # 노트북과 동일한 인증 방식
#                 )
#             response.raise_for_status()
            
#             # Watson SDK 호환을 위한 응답 객체
#             class TTSResponse:
#                 def __init__(self, content):
#                     self.content = content
            
#             return TTSResponse(response.content)
        
#         synthesis_result = await loop.run_in_executor(None, direct_tts_call)
        
#         # 오디오 데이터 추출
#         audio_content = synthesis_result.content
        
#         # 응답 생성
#         def generate():
#             yield audio_content
        
#         return StreamingResponse(
#             generate(),
#             media_type=f"audio/{audio_format}",
#             headers={
#                 "Content-Disposition": f"attachment; filename=tts_output.{audio_format}",
#                 "Content-Length": str(len(audio_content))
#             }
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"음성 합성 중 오류가 발생했습니다: {str(e)}"
#         )


# @router.post("/voice/chat", summary="음성 채팅 (STT + Chat + TTS)")
# async def voice_chat(
#     audio_file: UploadFile = File(..., description="사용자 음성 파일"),
#     underlying_diseases: str = Form(default="", description="기저질환 (쉼표로 구분)"),
#     current_medications: str = Form(default="", description="현재 복용 약물 (쉼표로 구분)"),
#     tts_voice: str = Form(default="ko-KR_HyunjunVoice", description="응답 음성"),
#     audio_format: str = Form(default="mp3", description="출력 오디오 형식")
# ):
#     """
#     음성 입력을 받아 STT → AI 채팅 → TTS 과정을 거쳐 음성 응답을 반환합니다.
    
#     완전한 음성 대화 파이프라인:
#     1. 음성 파일 → 텍스트 변환 (STT)
#     2. 텍스트 → AI 채팅 응답 생성
#     3. AI 응답 → 음성 변환 (TTS)
#     4. 음성 파일 반환
#     """
#     try:
#         # Step 1: STT (음성 → 텍스트)
#         file_content = await audio_file.read()
#         validation_result = validate_audio_file(file_content)
        
#         # 원본 파일의 MIME 타입 감지
#         original_type = validation_result.get('file_type', 'audio/unknown')
#         content_type_mapping = {
#             'audio/wav': 'audio/wav',
#             'audio/x-wav': 'audio/wav', 
#             'audio/mpeg': 'audio/mp3',
#             'audio/mp4': 'audio/mp4',
#             'audio/ogg': 'audio/ogg',
#             'audio/webm': 'audio/webm',
#             'audio/flac': 'audio/flac',
#             'audio/unknown': 'audio/wav'
#         }
#         watson_content_type = content_type_mapping.get(original_type, 'audio/wav')
        
#         # REST API 직접 호출로 STT 처리
#         def direct_stt_call_chat():
#             # Watson STT REST API 엔드포인트
#             stt_url = f"{settings.WATSON_STT_URL}/v1/recognize"
            
#             # Basic 인증 헤더 생성
#             auth_string = f"apikey:{settings.WATSON_STT_API_KEY}"
#             auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
            
#             headers = {
#                 'Authorization': f'Basic {auth_b64}',
#                 'Content-Type': watson_content_type
#             }
            
#             params = {
#                 'model': 'ko-KR_BroadbandModel'
#             }
            
#             with httpx.Client(timeout=60.0) as client:
#                 response = client.post(
#                     stt_url, 
#                     headers=headers, 
#                     params=params,
#                     content=file_content,
#                 )
#             response.raise_for_status()
            
#             return response.json()
        
#         loop = asyncio.get_event_loop()
        
#         recognition_result = await loop.run_in_executor(None, direct_stt_call_chat)
        
#         # STT 결과 확인
#         if not recognition_result.get('results') or not recognition_result['results'][0].get('alternatives'):
#             raise HTTPException(
#                 status_code=400,
#                 detail="음성을 인식할 수 없습니다. 더 명확하게 말씀해주세요."
#             )
        
#         user_text = recognition_result['results'][0]['alternatives'][0]['transcript'].strip()
#         stt_confidence = recognition_result['results'][0]['alternatives'][0].get('confidence', 0.0)
        
#         if not user_text:
#             raise HTTPException(
#                 status_code=400,
#                 detail="음성에서 텍스트를 추출할 수 없습니다."
#             )
        
#         # Step 2: AI 채팅 처리
#         # 사용자 컨텍스트 파싱
#         diseases_list = [d.strip() for d in underlying_diseases.split(',') if d.strip()] if underlying_diseases else []
#         medications_list = [m.strip() for m in current_medications.split(',') if m.strip()] if current_medications else []
        
#         # 채팅 요청 생성
#         chat_request = ChatRequest(
#             question=user_text,
#             underlying_diseases=diseases_list,
#             currentMedications=medications_list
#         )
        
#         # AI 채팅 응답 생성
#         chat_response = await get_chat_response(chat_request)
#         ai_response_text = chat_response["answer"]
        
#         # Step 3: TTS (텍스트 → 음성)
#         # REST API 직접 호출로 한국어 처리
#         def direct_tts_call_chat():
#             # 이모지 및 특수문자 제거 (TTS 호환성을 위해)
#             import re
            
#             # 완전한 ASCII 호환 텍스트 생성 (Latin-1 문제 완전 해결)
#             def make_tts_safe_text(text):
#                 import unicodedata
#                 import re
                
#                 # 1. 모든 이모지와 특수문자 완전 제거
#                 cleaned = ''.join(char for char in text if unicodedata.category(char) not in ['So', 'Sk', 'Sm', 'Cn'])
                
#                 # 2. 마크다운 제거
#                 cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
#                 cleaned = re.sub(r'\n+', ' ', cleaned)
#                 cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
#                 # 3. Latin-1로 인코딩 불가능한 모든 문자 찾아서 제거
#                 safe_chars = []
#                 for char in cleaned:
#                     try:
#                         char.encode('latin-1')
#                         safe_chars.append(char)
#                     except UnicodeEncodeError:
#                         # Latin-1로 인코딩 불가능한 문자는 공백으로 대체
#                         safe_chars.append(' ')
                
#                 # 4. 연속된 공백 정리
#                 final_text = ''.join(safe_chars)
#                 final_text = re.sub(r'\s+', ' ', final_text).strip()
                
#                 return final_text
            
#             # 텍스트 정리 (Latin-1 완전 호환)
#             cleaned_text = make_tts_safe_text(ai_response_text)  # 완전한 ASCII 호환 변환
            
#             print(f"정리된 TTS 텍스트: {repr(cleaned_text)}")
#             print(f"cleaned_text 타입: {type(cleaned_text)}")
#             print(f"cleaned_text 인코딩 테스트:")
#             try:
#                 print(f"  UTF-8 인코딩: OK")
#                 utf8_bytes = cleaned_text.encode('utf-8')
#                 print(f"  UTF-8 바이트 길이: {len(utf8_bytes)}")
#             except Exception as e:
#                 print(f"  UTF-8 인코딩 실패: {e}")
            
#             # Watson TTS REST API 엔드포인트 (voice는 URL 파라미터로)
#             tts_url = f"{settings.WATSON_TTS_URL}/v1/synthesize?voice={tts_voice}"
#             print(f"TTS URL: {tts_url}")
            
#             # Basic 인증 헤더 생성
#             auth_string = f"apikey:{settings.WATSON_TTS_API_KEY}"
#             auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
#             print(f"인증 헤더 생성: OK")
            
#             headers = {
#                 'Content-Type': 'application/json; charset=utf-8',
#                 'Accept': f'audio/{audio_format}',
#                 'Authorization': f'Basic {auth_b64}'
#             }
#             print(f"헤더: {headers}")
            
#             data = {
#                 'text': cleaned_text  # voice는 URL로 이동, text만 JSON에
#             }
#             print(f"데이터: {data}")
            
#             # 🔍 LATIN-1 오류 완전 추적 및 해결
#             print("🔍 Latin-1 인코딩 문제 완전 추적 시작...")
            
#             import json
#             import httpx
#             import traceback
            
#             try:
#                 # 1. 텍스트 문자 하나씩 Latin-1 호환성 검사
#                 print(f"🔤 텍스트 분석: {repr(cleaned_text[:50])}...")
#                 problematic_chars = []
#                 for i, char in enumerate(cleaned_text):
#                     try:
#                         char.encode('latin-1')
#                     except UnicodeEncodeError:
#                         problematic_chars.append((i, char, ord(char)))
#                         if len(problematic_chars) >= 5:  # 처음 5개만
#                             break
                
#                 if problematic_chars:
#                     print(f"❌ Latin-1 비호환 문자 발견: {problematic_chars}")
#                     # 문제 문자들을 완전히 제거
#                     for pos, char, code in problematic_chars:
#                         cleaned_text = cleaned_text.replace(char, ' ')
#                     # 연속 공백 정리
#                     import re
#                     cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
#                     print(f"🔧 문제 문자 제거 후: {repr(cleaned_text[:50])}...")
#                 else:
#                     print("✅ 모든 문자가 Latin-1 호환")
                
#                 # 2. Watson TTS API 정확한 파라미터 구성 (text만, voice는 URL에)
#                 data = {
#                     'text': cleaned_text
#                 }
                
#                 print(f"🎤 TTS 요청 음성: {tts_voice}")
#                 print(f"🎤 TTS 요청 형식: {audio_format}")
#                 print(f"🎤 TTS 요청 텍스트: {cleaned_text[:50]}...")
                
#                 # 3. 완벽한 UTF-8 JSON 직렬화
#                 json_data = json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'))
#                 json_bytes = json_data.encode('utf-8')
                
#                 print(f"🔤 최종 JSON: {json_data[:100]}...")
#                 print(f"🔤 UTF-8 바이트 수: {len(json_bytes)}")
                
#             except Exception as e:
#                 print(f"💥 텍스트 전처리 오류: {e}")
#                 traceback.print_exc()
#                 raise
            
#             # 2. HTTPX로 완전한 UTF-8 제어 (Authorization은 auth 파라미터로)
#             headers_utf8 = {
#                 'Content-Type': 'application/json; charset=utf-8',
#                 'Accept': f'audio/{audio_format}',
#                 'Content-Length': str(len(json_bytes))
#             }
            
#             print(f"🌐 HTTPX 헤더: {headers_utf8}")
            
#             try:
#                 print("🚀 HTTPX POST 요청 시작 (완전 UTF-8 제어)...")
                
#                 # HTTPX 클라이언트로 UTF-8 완전 제어 (노트북 방식 적용)
#                 with httpx.Client(timeout=30.0) as client:
#                     response = client.post(
#                         tts_url,
#                         headers=headers_utf8,
#                         content=json_bytes,  # 완전한 UTF-8 바이트 제어
#                         auth=('apikey', settings.WATSON_TTS_API_KEY)  # 노트북과 동일한 인증 방식
#                     )
                
#                 print(f"✅ HTTP 응답 상태: {response.status_code}")
#                 print(f"📄 HTTP 응답 헤더: {dict(response.headers)}")
                
#                 if response.status_code != 200:
#                     print(f"❌ HTTP 오류 응답: {response.text}")
                
#                 response.raise_for_status()
#                 print("🎉 HTTP 응답 성공!")
                
#             except httpx.RequestError as e:
#                 print(f"💥 HTTPX 요청 오류: {e}")
#                 print(f"📝 오류 타입: {type(e)}")
#                 traceback.print_exc()
#                 raise Exception(f"TTS API 호출 실패: {str(e)}")
#             except Exception as e:
#                 print(f"💥 예상치 못한 오류: {e}")
#                 print(f"🔍 오류 타입: {type(e)}")
#                 print(f"📊 오류 내용: {repr(str(e))}")
                
#                 # Latin-1 에러인지 확인
#                 if 'latin-1' in str(e).lower():
#                     print("🎯 Latin-1 인코딩 오류 확인!")
#                     print("🔍 에러 발생 위치 추적:")
#                     traceback.print_exc()
#                 else:
#                     traceback.print_exc()
#                 raise
            
#             # Watson SDK 호환 응답 객체
#             class TTSResponse:
#                 def __init__(self, content):
#                     self.content = content
            
#             return TTSResponse(response.content)
        
#         synthesis_result = await loop.run_in_executor(None, direct_tts_call_chat)
        
#         audio_content = synthesis_result.content
        
#         # 응답 생성
#         def generate():
#             yield audio_content
        
#         # HTTP 헤더는 ASCII만 지원 - 한글 텍스트 완전 제거
#         safe_headers = {
#             "Content-Disposition": f"attachment; filename=voice_chat_response.{audio_format}",
#             "Content-Length": str(len(audio_content)),
#             "X-STT-Confidence": str(stt_confidence),
#             "X-Agent-Used": chat_response.get("model_metadata", {}).get("agent_used", "Unknown"),
#             "X-Text-Length": str(len(user_text)),
#             "X-Response-Length": str(len(ai_response_text))
#         }
        
#         return StreamingResponse(
#             generate(),
#             media_type=f"audio/{audio_format}",
#             headers=safe_headers
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"음성 채팅 처리 중 오류가 발생했습니다: {str(e)}"
#         )


# @router.get("/voice/health", summary="음성 서비스 상태 확인")
# async def voice_health_check():
#     """음성 처리 서비스들의 상태를 확인합니다"""
    
#     health_status = {
#         "service": "Dr.Watson Voice API",
#         "stt_status": "unknown",
#         "tts_status": "unknown",
#         "config_status": {
#             "WATSON_STT_API_KEY": bool(settings.WATSON_STT_API_KEY),
#             "WATSON_TTS_API_KEY": bool(settings.WATSON_TTS_API_KEY),
#         }
#     }
    
#     # STT 서비스 상태 확인 (REST API 사용)
#     try:
#         def test_stt_connection():
#             stt_url = f"{settings.WATSON_STT_URL}/v1/models"
#             auth_string = f"apikey:{settings.WATSON_STT_API_KEY}"
#             auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
            
#             headers = {'Authorization': f'Basic {auth_b64}'}
#             with httpx.Client(timeout=10.0) as client:
#                 response = client.get(stt_url, headers=headers)
#             response.raise_for_status()
#             return response.json()
        
#         models = await asyncio.get_event_loop().run_in_executor(None, test_stt_connection)
#         health_status["stt_status"] = "healthy" if models.get('models') else "unavailable"
#     except Exception as e:
#         health_status["stt_status"] = "error"
#         health_status["stt_error"] = str(e)
    
#     # TTS 서비스 상태 확인 (REST API 사용)
#     try:
#         def test_tts_connection():
#             tts_url = f"{settings.WATSON_TTS_URL}/v1/voices"
#             auth_string = f"apikey:{settings.WATSON_TTS_API_KEY}"
#             auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
            
#             headers = {'Authorization': f'Basic {auth_b64}'}
#             with httpx.Client(timeout=10.0) as client:
#                 response = client.get(tts_url, headers=headers)
#             response.raise_for_status()
#             return response.json()
        
#         voices = await asyncio.get_event_loop().run_in_executor(None, test_tts_connection)
#         health_status["tts_status"] = "healthy" if voices.get('voices') else "unavailable"
#     except Exception as e:
#         health_status["tts_status"] = "error"
#         health_status["tts_error"] = str(e)
    
#     # 전체 상태 결정
#     overall_healthy = (
#         health_status["stt_status"] == "healthy" and 
#         health_status["tts_status"] == "healthy" and
#         health_status["config_status"]["WATSON_STT_API_KEY"] and
#         health_status["config_status"]["WATSON_TTS_API_KEY"]
#     )
    
#     health_status["status"] = "healthy" if overall_healthy else "degraded"
#     health_status["message"] = "모든 음성 서비스가 정상 작동 중입니다." if overall_healthy else "일부 음성 서비스에 문제가 있습니다."
    
#     return health_status