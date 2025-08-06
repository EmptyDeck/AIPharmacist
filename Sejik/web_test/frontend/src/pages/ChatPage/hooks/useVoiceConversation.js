import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";

export function useVoiceConversation({
  apiBaseUrl,
  onUserMessage,
  onBotMessage,
  autoStart = false,
  silenceThreshold = 0.000, // 침묵 임계값 (0-1)
  silenceDuration = 10000, // 침묵 지속 시간 (ms) Xms동안 침묵이 감지되면 녹음이 자동으로 중지됩니다.
  maxRecordingTime = 10000, // 최대 녹음 시간 (ms)
}) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const animationFrameRef = useRef(null);
  const lastSoundTimeRef = useRef(0);
  const maxRecordingTimerRef = useRef(null);

  // 오디오 레벨 분석 및 침묵 감지
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // 평균 볼륨 계산
    const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
    const normalizedVolume = average / 255; // 0-1 범위로 정규화

    const currentTime = Date.now();

    // 소리가 임계값을 넘으면 마지막 소리 시간 업데이트
    if (normalizedVolume > silenceThreshold) {
      lastSoundTimeRef.current = currentTime;
      
      // 기존 침묵 타이머가 있다면 제거
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    } 
    // 침묵 상태이고 타이머가 없다면 타이머 시작
    else if (!silenceTimerRef.current && lastSoundTimeRef.current > 0) {
      const silenceTime = currentTime - lastSoundTimeRef.current;
      
      if (silenceTime >= silenceDuration) {
        console.log(`[🔇] 침묵 감지됨 (${silenceTime}ms) → 녹음 중지 및 전송 시작`);
        stopRecordingAndSend();
        return;
      } else {
        // 남은 침묵 시간만큼 타이머 설정
        const remainingTime = silenceDuration - silenceTime;
        console.log(`[⏱️] 침묵 타이머 시작 (${remainingTime}ms 남음)`);
        
        silenceTimerRef.current = setTimeout(() => {
          console.log("[🔇] 침묵 타이머 완료 → 녹음 중지 및 전송 시작");
          stopRecordingAndSend();
        }, remainingTime);
      }
    }

    // 다음 프레임에서 다시 분석
    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(analyzeAudio);
    }
  }, [silenceThreshold, silenceDuration, isRecording]);

  // 오디오 컨텍스트 및 분석기 설정
  const setupAudioAnalysis = useCallback((stream) => {
    try {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      analyserRef.current.smoothingTimeConstant = 0.8;
      
      console.log("[🎵] 오디오 분석기 설정 완료");
      
      // 분석 시작
      lastSoundTimeRef.current = Date.now();
      analyzeAudio();
    } catch (error) {
      console.error("[❌] 오디오 분석기 설정 실패:", error);
    }
  }, [analyzeAudio]);

  // 녹음 시작
  const startRecording = useCallback(async () => {
    if (isRecording) {
      console.log("[🎤] 이미 녹음 중, 중복 시작 방지");
      return;
    }

    console.log("[🎤] 녹음 시작 요청됨");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      
      streamRef.current = stream;
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "audio/webm" });
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          console.log(`[📦] 오디오 청크 수신 (${e.data.size} bytes)`);
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstart = () => {
        console.log("[🎙️] 녹음 시작됨");
        setIsRecording(true);
        setupAudioAnalysis(stream);
        
        // 최대 녹음 시간 타이머 설정
        maxRecordingTimerRef.current = setTimeout(() => {
          console.log(`[⏰] 최대 녹음 시간 (${maxRecordingTime}ms) 도달 → 강제 중지`);
          stopRecordingAndSend();
        }, maxRecordingTime);
      };

      mediaRecorderRef.current.onstop = async () => {
        console.log("[🛑] 녹음 중지됨");
        setIsRecording(false);

        // 최대 녹음 시간 타이머 정리
        if (maxRecordingTimerRef.current) {
          clearTimeout(maxRecordingTimerRef.current);
          maxRecordingTimerRef.current = null;
        }

        // 분석 중지
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }

        // 오디오 컨텍스트 정리
        if (audioContextRef.current) {
          try {
            await audioContextRef.current.close();
            audioContextRef.current = null;
            analyserRef.current = null;
          } catch (error) {
            console.warn("[⚠️] 오디오 컨텍스트 정리 중 오류:", error);
          }
        }

        // 스트림 정리
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }

        if (audioChunksRef.current.length === 0) {
          console.warn("[⚠️] 오디오 청크 없음 → 전송 생략");
          if (autoStart) startRecording();
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        console.log("[📤] 녹음된 오디오 Blob 생성 완료");

        // --- 1. STT ---
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        let sttText = "";
        try {
          console.log("[🧠] STT 요청 전송 중...");
          const sttRes = await axios.post(`${apiBaseUrl}/api/audio/stt`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
          sttText = sttRes.data.text || "";
          console.log("[✅] STT 응답 수신:", sttText);
        } catch (e) {
          console.error("[❌] STT 요청 실패:", e);
        }

        if (!sttText) {
          console.warn("[⚠️] STT 결과 없음 → 자동 재녹음 여부:", autoStart);
          if (autoStart) startRecording();
          return;
        }

        if (onUserMessage) {
          console.log("[📩] 사용자 메시지 전달:", sttText);
          onUserMessage(sttText);
        }

        // --- 2. GPT ---
        let gptText = "";
        try {
          console.log("[🤖] GPT 요청 전송 중...");
          const gptRes = await axios.post(
            `${apiBaseUrl}/api/audio/gpt`,
            { message: sttText },
            { headers: { "Content-Type": "application/json" } }
          );
          gptText = gptRes.data.text || "";
          console.log("[✅] GPT 응답 수신:", gptText);
        } catch (e) {
          console.error("[❌] GPT 요청 실패:", e);
          gptText = "죄송합니다. 답변을 생성하지 못했습니다.";
        }

        if (onBotMessage) {
          console.log("[📩] 봇 메시지 전달:", gptText);
          onBotMessage(gptText);
        }

        // --- 3. TTS ---
        try {
          console.log("[🔊] TTS 요청 전송 중...");
          const ttsRes = await axios.post(
            `${apiBaseUrl}/api/audio/tts`,
            { text: gptText },
            { responseType: "blob" }
          );
          const audioUrl = URL.createObjectURL(ttsRes.data);
          const audio = new Audio(audioUrl);
          console.log("[🎧] TTS 오디오 재생 시작");
          audio.play();

          audio.onended = () => {
            console.log("[🎧] TTS 오디오 재생 완료");
            if (autoStart) {
              console.log("[🔄] 자동 재시작 → 녹음 재개");
              startRecording();
            }
          };
        } catch (e) {
          console.error("[❌] TTS 요청 실패:", e);
          if (autoStart) {
            console.log("[🔄] 자동 재시작 → 녹음 재개");
            startRecording();
          }
        }
      };

      mediaRecorderRef.current.start();
      console.log("[🎬] mediaRecorder.start() 호출됨");
    } catch (err) {
      console.error("[❌] 마이크 권한 에러 또는 녹음 오류:", err);
    }
  }, [apiBaseUrl, autoStart, onBotMessage, onUserMessage, setupAudioAnalysis, isRecording]);

  // 녹음 중지 함수
  const stopRecordingAndSend = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      console.log("[🛑] 녹음 종료 요청됨");
      
      // 타이머 정리
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      
      // 애니메이션 프레임 정리
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      
      mediaRecorderRef.current.stop();
    }
  }, []);

  // 토글 함수
  const toggleRecording = useCallback(() => {
    if (isRecording) {
      console.log("[🛑] toggle → 녹음 중지");
      stopRecordingAndSend();
    } else {
      console.log("[🎙️] toggle → 녹음 시작");
      startRecording();
    }
  }, [isRecording, startRecording, stopRecordingAndSend]);

  // 언마운트 시 정리
  useEffect(() => {
    return () => {
      console.log("[🧹] 컴포넌트 언마운트 → 리소스 정리");
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(console.warn);
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return {
    isRecording,
    startRecording,
    stopRecording: stopRecordingAndSend,
    toggleRecording,
  };
}