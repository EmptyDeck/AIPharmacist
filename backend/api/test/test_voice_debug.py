"""
음성채팅 디버깅 테스트 파일
각 단계별로 상세한 로그를 출력하여 오류 지점을 찾습니다.
"""

import sys
import os
import asyncio
import json
import traceback

# 프로젝트 루트 경로를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))  # api/test/
api_dir = os.path.dirname(current_dir)                   # api/
backend_dir = os.path.dirname(api_dir)                   # backend/
sys.path.insert(0, backend_dir)

print(f"현재 디렉토리: {current_dir}")
print(f"백엔드 디렉토리: {backend_dir}")
print(f"sys.path에 추가됨: {backend_dir}")

from core.config import settings
from api.chat import get_chat_response
from schemas.chat import ChatRequest
import httpx
import base64
import re
import unicodedata


class VoiceChatDebugger:
    def __init__(self):
        self.step = 0
        print("=" * 60)
        print("🎤 음성채팅 디버깅 테스트 시작")
        print("=" * 60)
    
    def log_step(self, title, content=""):
        self.step += 1
        print(f"\n📝 Step {self.step}: {title}")
        print("-" * 40)
        if content:
            print(content)
    
    def log_success(self, message):
        print(f"✅ {message}")
    
    def log_error(self, message, error=None):
        print(f"❌ {message}")
        if error:
            print(f"   오류 내용: {error}")
            print(f"   오류 타입: {type(error)}")
    
    def test_config(self):
        """설정 값 테스트"""
        self.log_step("설정 값 확인")
        
        print(f"WATSON_STT_API_KEY: {'✅ 설정됨' if settings.WATSON_STT_API_KEY else '❌ 없음'}")
        print(f"WATSON_STT_URL: {settings.WATSON_STT_URL}")
        print(f"WATSON_TTS_API_KEY: {'✅ 설정됨' if settings.WATSON_TTS_API_KEY else '❌ 없음'}")
        print(f"WATSON_TTS_URL: {settings.WATSON_TTS_URL}")
    
    def test_text_processing(self, sample_text):
        """텍스트 처리 테스트"""
        self.log_step("텍스트 처리 테스트", f"원본 텍스트: {repr(sample_text)}")
        
        try:
            # 이모지 제거 함수
            def remove_emojis_and_symbols(text):
                import unicodedata
                
                # 1. 유니코드 카테고리로 이모지 제거
                cleaned = ''.join(char for char in text if unicodedata.category(char) not in ['So', 'Sk', 'Sm'])
                
                # 2. 알려진 문제 이모지들 직접 제거
                emojis = ['📋', '💊', '📏', '🔄', '⏰', '📅', '📝', '⚠️', '✅', '❌', '🎯', '🌟', '🔍', '📡', '🚀', '😊']
                for emoji in emojis:
                    cleaned = cleaned.replace(emoji, ' ')
                
                # 3. 마크다운 제거
                cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
                cleaned = re.sub(r'\n+', ' ', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                # 4. 🚨 강제 ASCII 변환 (한국어 → 영어)
                korean_to_english = {
                    '복약': 'medication', '정보': 'information', '분석': 'analysis', '결과': 'result',
                    '약물명': 'medication name', '용량': 'dosage', '복용': 'take', '횟수': 'frequency',
                    '시간': 'time', '기간': 'duration', '일': 'days', '특별': 'special',
                    '지시사항': 'instructions', '없음': 'none', '아침': 'morning', '점심': 'lunch',
                    '저녁': 'evening', '하루': 'daily', '번': 'times', '정': 'tablet',
                    '추가': 'add', '캘린더': 'calendar', '알림': 'notification', '일정': 'schedule',
                    '등록': 'register', '취소': 'cancel', '정확한': 'accurate', '의사': 'doctor',
                    '약사': 'pharmacist', '지시': 'instruction', '우선': 'priority', '따르세요': 'follow'
                }
                
                # 한국어를 영어로 변환
                for korean, english in korean_to_english.items():
                    cleaned = cleaned.replace(korean, english)
                
                # 5. 남은 비ASCII 문자 제거
                ascii_only = ''.join(char for char in cleaned if ord(char) < 128)
                ascii_only = re.sub(r'\s+', ' ', ascii_only).strip()
                
                print(f"🔤 ASCII 변환 완료: {repr(ascii_only)}")
                return ascii_only
            
            cleaned_text = remove_emojis_and_symbols(sample_text)
            
            print(f"정리된 텍스트: {repr(cleaned_text)}")
            print(f"정리된 텍스트 길이: {len(cleaned_text)}")
            print(f"정리된 텍스트 타입: {type(cleaned_text)}")
            
            # 인코딩 테스트
            try:
                utf8_bytes = cleaned_text.encode('utf-8')
                self.log_success(f"UTF-8 인코딩 성공 ({len(utf8_bytes)} 바이트)")
            except Exception as e:
                self.log_error("UTF-8 인코딩 실패", e)
                
            try:
                latin1_bytes = cleaned_text.encode('latin-1')
                self.log_success(f"Latin-1 인코딩 성공 ({len(latin1_bytes)} 바이트)")
            except Exception as e:
                self.log_error("Latin-1 인코딩 실패", e)
                print("👆 이것이 원인일 수 있습니다!")
                
                # 문제 문자 찾기
                print("문제 문자들 분석:")
                for i, char in enumerate(cleaned_text):
                    try:
                        char.encode('latin-1')
                    except:
                        print(f"  위치 {i}: {repr(char)} (유니코드: U+{ord(char):04X})")
            
            return cleaned_text
            
        except Exception as e:
            self.log_error("텍스트 처리 실패", e)
            traceback.print_exc()
            return None
    
    def test_http_request_preparation(self, text, voice="ko-KR_JinV3Voice", audio_format="mp3"):
        """HTTP 요청 준비 테스트"""
        self.log_step("HTTP 요청 준비")
        
        try:
            # URL 구성
            tts_url = f"{settings.WATSON_TTS_URL}/v1/synthesize"
            print(f"TTS URL: {tts_url}")
            
            # 인증 헤더 생성 (전체 API 키 사용)
            auth_string = f"apikey:{settings.WATSON_TTS_API_KEY}"
            auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
            print(f"API 키 길이: {len(settings.WATSON_TTS_API_KEY)} 문자")
            print(f"인증 문자열 인코딩: ✅")
            
            # 헤더 구성
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': f'audio/{audio_format}',
                'Authorization': f'Basic {auth_b64}'
            }
            print(f"헤더 구성: {headers}")
            
            # 데이터 구성
            data = {
                'text': text,
                'voice': voice
            }
            print(f"요청 데이터: {data}")
            
            # JSON 직렬화 테스트
            try:
                json_str = json.dumps(data, ensure_ascii=False)
                self.log_success(f"JSON 직렬화 성공 ({len(json_str)} 문자)")
                print(f"JSON: {json_str[:100]}...")
            except Exception as e:
                self.log_error("JSON 직렬화 실패", e)
                return None
            
            return tts_url, headers, data
            
        except Exception as e:
            self.log_error("HTTP 요청 준비 실패", e)
            traceback.print_exc()
            return None
    
    def test_http_request(self, tts_url, headers, data):
        """실제 HTTP 요청 테스트"""
        self.log_step("HTTP 요청 실행")
        
        try:
            print("🌐 Watson TTS API 호출 중...")
            
            # requests.post 호출 전 마지막 체크
            print(f"URL: {tts_url}")
            print(f"Headers: {headers}")
            print(f"Data keys: {list(data.keys())}")
            print(f"Text length: {len(data['text'])}")
            
            # HTTPX를 사용한 UTF-8 완전 제어
            import json
            json_data = json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'))
            json_bytes = json_data.encode('utf-8')
            
            headers_httpx = headers.copy()
            headers_httpx['Content-Length'] = str(len(json_bytes))
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    tts_url,
                    headers=headers_httpx,
                    content=json_bytes,
                )
            
            print(f"HTTP 상태 코드: {response.status_code}")
            print(f"응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                self.log_success(f"TTS 요청 성공! 음성 데이터: {len(response.content)} 바이트")
                return response.content
            else:
                self.log_error(f"HTTP 오류 {response.status_code}", response.text)
                return None
                
        except httpx.RequestError as e:
            self.log_error("HTTP 요청 실패", e)
            if hasattr(e, 'response') and e.response:
                print(f"응답 내용: {e.response.text}")
            traceback.print_exc()
            return None
        except Exception as e:
            self.log_error("예상치 못한 오류", e)
            traceback.print_exc()
            return None
    
    async def test_full_chat_flow(self):
        """전체 채팅 플로우 테스트"""
        self.log_step("전체 채팅 플로우 테스트")
        
        try:
            # 샘플 채팅 요청 생성
            chat_request = ChatRequest(
                question="매일 아침에 혈압약 1정씩 복용하세요",
                underlying_diseases=["고혈압"],
                currentMedications=["혈압약"]
            )
            
            print(f"채팅 요청: {chat_request}")
            
            # AI 응답 생성
            print("🤖 AI 응답 생성 중...")
            chat_response = await get_chat_response(chat_request)
            
            ai_response_text = chat_response["answer"]
            print(f"AI 응답: {ai_response_text[:200]}...")
            
            # 텍스트 처리
            cleaned_text = self.test_text_processing(ai_response_text)
            if not cleaned_text:
                return False
            
            # HTTP 요청 준비
            request_data = self.test_http_request_preparation(cleaned_text)
            if not request_data:
                return False
            
            tts_url, headers, data = request_data
            
            # HTTP 요청 실행
            audio_content = self.test_http_request(tts_url, headers, data)
            if audio_content:
                self.log_success("전체 플로우 성공!")
                return True
            else:
                return False
                
        except Exception as e:
            self.log_error("전체 플로우 실패", e)
            traceback.print_exc()
            return False


async def main():
    """메인 테스트 함수"""
    debugger = VoiceChatDebugger()
    
    # 1. 설정 확인
    debugger.test_config()
    
    # 2. 샘플 텍스트로 텍스트 처리 테스트
    sample_text = """
📋 **복약 정보 분석 결과:**

💊 **약물명**: 혈압약
📏 **용량**: 1정
🔄 **복용 횟수**: 하루 1번
⏰ **복용 시간**: 아침
📅 **복용 기간**: 7일
📝 **특별 지시사항**: 빈 복용 없음

위 정보로 Google Calendar에 복약 알림을 추가하시겠습니까?

**"네, 추가해주세요"** 또는 **"추가"**라고 답하시면 캘린더에 일정 등록해드립니다.
**"아니요"** 또는 **"취소"**라고 답하시면 취소됩니다.

⚠️ 정확한 복약을 위해 의사나 약사의 지시를 우선으로 따르세요.
"""
    
    cleaned_text = debugger.test_text_processing(sample_text)
    
    if cleaned_text:
        # 3. HTTP 요청 테스트
        request_data = debugger.test_http_request_preparation(cleaned_text)
        if request_data:
            tts_url, headers, data = request_data
            debugger.test_http_request(tts_url, headers, data)
    
    # 4. 전체 플로우 테스트
    print("\n" + "="*60)
    print("🔄 전체 플로우 테스트")
    print("="*60)
    
    success = await debugger.test_full_chat_flow()
    
    print("\n" + "="*60)
    if success:
        print("🎉 모든 테스트 통과!")
    else:
        print("💥 테스트 실패 - 위 로그를 확인하세요.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())