// hooks/useVoiceRecorder.js
import { useState, useRef, useCallback } from 'react';

export const useVoiceRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const animationFrameRef = useRef(null);

  // 침묵 감지 설정
  const SILENCE_THRESHOLD = 0.01; // 음량 임계값 (0~1)
  const SILENCE_DURATION = 2000;  // 침묵 지속 시간 (ms)

  // 실시간 음량 분석
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // 평균 음량 계산
    const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
    const normalizedLevel = average / 255;
    
    setAudioLevel(normalizedLevel);

    // 침묵 감지
    if (normalizedLevel < SILENCE_THRESHOLD) {
      if (!silenceTimerRef.current) {
        silenceTimerRef.current = setTimeout(() => {
          if (isRecording) {
            stopRecording();
          }
        }, SILENCE_DURATION);
      }
    } else {
      // 소리가 감지되면 침묵 타이머 초기화
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    }

    animationFrameRef.current = requestAnimationFrame(analyzeAudio);
  }, [isRecording]);

  // 녹음 시작
  const startRecording = useCallback(async () => {
    try {
      // 마이크 권한 요청
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });
      
      streamRef.current = stream;

      // AudioContext 설정 (음량 분석용)
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      // MediaRecorder 설정
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : 'audio/wav';
      
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: mimeType });
        // 녹음 완료 콜백 실행
        if (onRecordingComplete) {
          onRecordingComplete(audioBlob);
        }
      };

      // 녹음 시작
      mediaRecorderRef.current.start();
      setIsRecording(true);

      // 실시간 음량 분석 시작
      analyzeAudio();

      return true;
    } catch (error) {
      console.error('녹음 시작 실패:', error);
      throw error;
    }
  }, [analyzeAudio]);

  // 녹음 중지
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }

    // 스트림 정리
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    // AudioContext 정리
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    // 타이머 정리
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    // 애니메이션 프레임 정리
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    setIsRecording(false);
    setAudioLevel(0);
  }, [isRecording]);

  // 강제 중지 (사용자가 토글 끄기)
  const forceStop = useCallback(() => {
    stopRecording();
  }, [stopRecording]);

  // 녹음 완료 콜백 설정
  let onRecordingComplete = null;
  const setOnRecordingComplete = useCallback((callback) => {
    onRecordingComplete = callback;
  }, []);

  return {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    forceStop,
    setOnRecordingComplete
  };
};