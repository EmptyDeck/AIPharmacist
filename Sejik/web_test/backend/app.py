from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from ibm_watson_machine_learning.foundation_models import Model
from dotenv import load_dotenv
import requests
import json
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Flask 앱 및 CORS 초기화
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# 환경 변수 불러오기 및 선언
load_dotenv()

STT_URL = os.getenv("STT_URL")
STT_API_KEY = os.getenv("STT_API_KEY")
TTS_URL = os.getenv("TTS_URL")
TTS_API_KEY = os.getenv("TTS_API_KEY")

IBM_CLOUD_URL = os.getenv("IBM_CLOUD_URL")
API_KEY = os.getenv("API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
MODEL_ID = os.getenv("MODEL_ID")

print("=== 환경 변수 체크 ===")
print(f"STT_URL: {'✓' if STT_URL else '✗'}")
print(f"STT_API_KEY: {'✓' if STT_API_KEY else '✗'}")
print(f"TTS_URL: {'✓' if TTS_URL else '✗'}")
print(f"TTS_API_KEY: {'✓' if TTS_API_KEY else '✗'}")
print(f"IBM_CLOUD_URL: {'✓' if IBM_CLOUD_URL else '✗'}")
print(f"API_KEY: {'✓' if API_KEY else '✗'}")
print(f"PROJECT_ID: {'✓' if PROJECT_ID else '✗'}")
print(f"MODEL_ID: {'✓' if MODEL_ID else '✗'}", end="")
print("Model name : " + MODEL_ID)
print("==================")

# LLM 모델 객체 초기화
try:
    generate_params = {GenParams.MAX_NEW_TOKENS: 900}
    model = Model(
        model_id=MODEL_ID,
        params=generate_params,
        credentials={"apikey": API_KEY, "url": IBM_CLOUD_URL},
        project_id=PROJECT_ID
    )
    print("✓ LLM 모델 초기화 성공")
except Exception as e:
    print(f"✗ LLM 모델 초기화 실패: {e}")
    model = None

# 음성파일 저장 폴더
VOICE_FOLDER = os.path.abspath('./voice_tmp')
os.makedirs(VOICE_FOLDER, exist_ok=True)


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Voice Chat API is running'})

# STT 함수


def speech_to_text(audio_file):
    print(f"STT 시작 - 파일: {audio_file}")

    if not STT_URL or not STT_API_KEY:
        print("✗ STT 환경변수 없음")
        return "Error: STT credentials not configured."

    try:
        headers = {"Content-Type": "audio/webm"}
        endpoint = f"{STT_URL}/v1/recognize"
        with open(audio_file, 'rb') as f:
            print(f"STT API 호출: {endpoint}")
            response = requests.post(
                endpoint,
                headers=headers,
                data=f,
                auth=("apikey", STT_API_KEY),
                timeout=30
            )
        print(f"STT 응답 상태코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"STT 응답: {result}")
            if result.get("results"):
                transcript = result["results"][0]["alternatives"][0]["transcript"]
                print(f"✓ STT 성공: {transcript}")
                return transcript
            else:
                print("✗ STT 결과 없음")
                return "Error: No speech detected."
        else:
            print(f"✗ STT API 오류: {response.status_code} - {response.text}")
            return f"Error: STT API failed with status {response.status_code}"

    except Exception as e:
        print(f"✗ STT 예외 발생: {e}")
        return f"Error transcribing audio: {str(e)}"


# LLM 답변 생성


def generate_response(text):
    print(f"LLM 시작 - 입력: {text}")

    if not model:
        print("✗ LLM 모델 없음")
        return "Error: LLM model not initialized."

    try:
        system_prompt = "You are a helpful assistant."
        formatted_prompt = f"<<SYS>>\n{system_prompt.strip()}\n<</SYS>>\n\n[INST]{text.strip()}[/INST]"

        print("LLM API 호출 중...")
        response = model.generate(prompt=formatted_prompt)
        result = response["results"][0]["generated_text"].strip()
        print(f"✓ LLM 성공: {result}")
        return result

    except Exception as e:
        print(f"✗ LLM 예외 발생: {e}")
        return f"Error generating response: {str(e)}"

# TTS 함수


def text_to_speech(text):
    print(f"TTS 시작 - 텍스트: {text}")

    if not TTS_URL or not TTS_API_KEY:
        print("✗ TTS 환경변수 없음")
        return None

    try:
        endpoint = f"{TTS_URL}/v1/synthesize"  # <<<< 엔드포인트명확화!
        headers = {
            "Content-Type": "application/json",
            "Accept": "audio/wav"
        }
        payload = {
            "text": text
        }
        params = {
            "voice": "en-US_MichaelV3Voice"
        }

        print(f"TTS API 호출: {endpoint}")
        response = requests.post(
            endpoint,
            headers=headers,
            params=params,        # <<<< voice 파라미터는 params로!
            json=payload,         # <<<< 본문은 json으로!
            auth=("apikey", TTS_API_KEY),
            timeout=30,
            stream=True           # chunk 단위로 받으면 더 안전함
        )

        print(f"TTS 응답 상태코드: {response.status_code}")

        if response.status_code == 200:
            out_path = os.path.join(VOICE_FOLDER, "output.wav")
            with open(out_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"✓ TTS 성공: {out_path}")
            return "output.wav"
        else:
            print(f"✗ TTS API 오류: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"✗ TTS 예외 발생: {e}")
        return None


# 음성대화 엔드포인트


@app.route('/api/voicechat', methods=['POST', 'OPTIONS'])
def voicechat():
    print("=== VoiceChat API 호출됨 ===")

    try:
        # CORS preflight 처리
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            response.headers.add(
                'Access-Control-Allow-Origin', 'http://localhost:3000')
            response.headers.add(
                'Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add(
                'Access-Control-Allow-Methods', 'POST, OPTIONS')
            return response

        if 'audio' not in request.files:
            print("✗ 오디오 파일 없음")
            return jsonify({'error': 'No audio file provided'}), 400

        # 파일 저장
        f = request.files['audio']
        print(f"파일 받음: {f.filename}")
        in_path = os.path.join(VOICE_FOLDER, 'input.wav')
        f.save(in_path)
        print(f"파일 저장: {in_path}")

        # 1. STT
        print("1단계: STT 시작")
        user_text = speech_to_text(in_path)
        if "Error" in user_text:
            print(f"STT 실패: {user_text}")
            return jsonify({'error': 'Speech recognition failed', 'details': user_text}), 500

        # 2. LLM → 응답 생성
        print("2단계: LLM 시작")
        ai_response = generate_response(user_text)
        if "Error" in ai_response:
            print(f"LLM 실패: {ai_response}")
            return jsonify({'error': 'LLM failed', 'details': ai_response}), 500

        # 3. TTS → 음성 파일 생성
        print("3단계: TTS 시작")
        output_audio_path = text_to_speech(ai_response)
        out_path = os.path.join(VOICE_FOLDER, 'output.wav')

        if not output_audio_path or not os.path.exists(out_path):
            print("TTS 실패")
            return jsonify({'error': 'TTS failed'}), 500

        print("✓ 모든 단계 성공")
        return jsonify({'audio': 'output.wav'})

    except Exception as e:
        print(f"✗ 전체 프로세스 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# 음성파일 다운/재생 엔드포인트


@app.route('/api/audio/<filename>')
def get_audio(filename):
    return send_from_directory(VOICE_FOLDER, filename, mimetype='audio/wav')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
