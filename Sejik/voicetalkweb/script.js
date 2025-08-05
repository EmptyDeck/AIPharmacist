// ====== 환경 설정 (API 키: 실제 키로 교체하세요. 보안상 서버로 옮기세요) ======
const TTS_API_KEY = 'HdyjTuGXQOK8xoBfZARtvdaqOeEbZoLLad2FLCKCc2Jx';  // os.getenv('TTS_API_KEY')
const TTS_URL = 'https://api.us-south.text-to-speech.watson.cloud.ibm.com/instances/5421e28b-1e74-4f93-9c05-808dcd0b7ca7';  // os.getenv('TTS_URL')
const STT_API_KEY = 'lkDU8YLMlsM151S0B4gPGoYOg10KMm1GVeQl9u_zKqO0';  // os.getenv('STT_API_KEY')
const STT_URL = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/2a088970-da1a-4ff1-b35e-988423300d08';  // os.getenv('STT_URL')
const IBM_URL = 'https://us-south.ml.cloud.ibm.com/';  // os.getenv('IBM_URL')
const PROJECT_ID = 'ca4ab8b0-0c39-4985-9400-2df348bbf894';  // os.getenv('PROJECT_ID')
const API_KEY = 'Q07iDID0ogWVEBA_cDtcEshvkcyqwF5HIzV75YOID-K8';  // os.getenv('API_KEY')

// ====== 상수 (Python과 유사) ======
const SAMPLE_RATE = 16000;  // RATE
const CHUNK_SIZE = 1024;    // CHUNK
const SILENCE_THRESHOLD = 0.1;  // Python의 1000을 normalized (0-1 범위)로 조정
const SILENCE_DURATION = 1000;   // 1초 (ms)
const MAX_RECORD_SECONDS = 10;   // RECORD_SECONDS

let isVoiceMode = false;
let mediaRecorder;
let audioContext;
let analyser;
let stream;
let silenceStart;
let isSilent = false;
let audioChunks = [];

// UI 요소
const toggleButton = document.getElementById('toggleVoice');
const statusDiv = document.getElementById('status');
const responseDiv = document.getElementById('response');
const ttsPlayer = document.getElementById('ttsPlayer');

// ====== 음성 모드 토글 ======
toggleButton.addEventListener('click', async () => {
    if (!isVoiceMode) {
        try {
            await startVoiceMode();
            isVoiceMode = true;
            toggleButton.textContent = 'Stop Voice Mode';
            statusDiv.textContent = '음성 모드 활성화. 말씀해주세요...';
        } catch (error) {
            console.error('음성 모드 시작 실패:', error);
            statusDiv.textContent = '마이크 권한이 필요합니다.';
        }
    } else {
        stopVoiceMode();
        isVoiceMode = false;
        toggleButton.textContent = 'Start Voice Mode';
        statusDiv.textContent = '준비 중...';
    }
});

// ====== 음성 모드 시작 (녹음 + 침묵 감지) ======
async function startVoiceMode() {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext();
    analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);
    analyser.fftSize = 2048;

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
    mediaRecorder.onstop = processRecording;

    audioChunks = [];
    silenceStart = Date.now();
    mediaRecorder.start();
    detectSilence();  // 침묵 감지 루프 시작
}

// ====== 침묵 감지 (Python의 is_silent 루프) ======
function detectSilence() {
    if (!isVoiceMode) return;

    const dataArray = new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(dataArray);
    const volume = Math.max(...dataArray) / 100 + 1;  // Normalize to 0-1

    if (volume < SILENCE_THRESHOLD) {
        if (!isSilent) {
            silenceStart = Date.now();
            isSilent = true;
        }
        if (Date.now() - silenceStart > SILENCE_DURATION) {
            mediaRecorder.stop();  // 침묵 시 녹음 종료
            return;
        }
    } else {
        isSilent = false;
    }

    // 최대 시간 초과 체크
    if (Date.now() - silenceStart > MAX_RECORD_SECONDS * 1000) {
        mediaRecorder.stop();
        statusDiv.textContent = '녹음 시간 초과';
        return;
    }

    requestAnimationFrame(detectSilence);  // 루프
}

// ====== 녹음 종료 및 처리 (STT → LLM → TTS) ======
async function processRecording() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    statusDiv.textContent = '음성 처리 중...';

    try {
        // STT: 음성 → 텍스트
        const userText = await speechToText(audioBlob);
        if (!userText) throw new Error('음성 인식 실패');

        statusDiv.textContent = `사용자: ${userText}`;
        console.log('👤 사용자의 말:', userText);

        // LLM: AI 응답 생성
        const prompt = userText + " 당신은 의사입니다. 환자의 질문에 답해주세요.";
        const aiResponse = await getCompletion(prompt);
        responseDiv.textContent = `Dr. Watson: ${aiResponse}`;
        console.log('🤖 응답:', aiResponse);

        // TTS: 텍스트 → 음성 재생
        await textToSpeech(aiResponse);
    } catch (error) {
        console.error('처리 실패:', error);
        statusDiv.textContent = '오류 발생: ' + error.message;
    } finally {
        // 자동 재녹음 (Python의 while True처럼)
        if (isVoiceMode) {
            audioChunks = [];
            mediaRecorder.start();
            silenceStart = Date.now();
            detectSilence();
            statusDiv.textContent = '다시 말씀해주세요...';
        }
    }
}

// ====== STT (음성 → 텍스트, IBM Watson) ======
async function speechToText(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recorded.wav');
    const sttModel = 'ko-KR_BroadbandModel';
    const sttEndpoint = `${STT_URL}/v1/recognize?model=${sttModel}`;

    const response = await fetch(sttEndpoint, {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: formData,
        // auth: fetch는 Basic Auth 사용 (apikey:STT_API_KEY)
        credentials: 'include'  // 필요 시
    });

    if (response.ok) {
        const result = await response.json();
        const recognized = result.results?.[0]?.alternatives?.[0]?.transcript;
        return recognized || '';
    }
    throw new Error('STT 실패: ' + response.status);
}

// ====== LLM (IBM Watson ML API 호출) ======
async function getCompletion(prompt) {
    const response = await fetch(`${IBM_URL}/ml/v1/text/generation?version=2023-05-29`, {  // IBM API 엔드포인트 (버전에 맞게 조정)
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
            'IBM-Project-ID': PROJECT_ID
        },
        body: JSON.stringify({
            model_id: 'ibm/granite-3-3-8b-instruct',
            input: prompt,
            parameters: {
                max_new_tokens: 200,
                temperature: 0.7
            }
        })
    });

    if (response.ok) {
        const data = await response.json();
        return data.results[0].generated_text;
    }
    throw new Error('LLM 실패: ' + response.status);
}

// ====== TTS (텍스트 → 음성, IBM Watson) ======
async function textToSpeech(text) {
    const ttsVoice = 'ko-KR_JinV3Voice';
    const endpoint = `${TTS_URL}/v1/synthesize?voice=${ttsVoice}`;

    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'audio/webm'
        },
        body: JSON.stringify({ text }),
        // auth: fetch는 Basic Auth 사용 (apikey:TTS_API_KEY)
        credentials: 'include'
    });

    if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        ttsPlayer.src = audioUrl;
        ttsPlayer.play();
        statusDiv.textContent = '응답 재생 중...';
    } else {
        throw new Error('TTS 실패: ' + response.status);
    }
}

// ====== 음성 모드 종료 ======
function stopVoiceMode() {
    if (mediaRecorder) mediaRecorder.stop();
    if (stream) stream.getTracks().forEach(track => track.stop());
    if (audioContext) audioContext.close();
    ttsPlayer.pause();
}
