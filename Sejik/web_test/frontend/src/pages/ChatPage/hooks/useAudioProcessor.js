// hooks/useAudioProcessor.js
import { useState, useCallback } from 'react';

export const useAudioProcessor = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);

  // 오디오 Blob을 WebM 형식으로 변환 (필요시)
  const convertToWebM = useCallback((audioBlob) => {
    // 이미 WebM 형식이면 그대로 반환
    if (audioBlob.type.includes('webm')) {
      return audioBlob;
    }

    // WAV to WebM 변환이 필요한 경우
    // 브라우저에서는 MediaRecorder가 자동으로 적절한 형식을 선택하므로
    // 대부분의 경우 추가 변환이 불필요
    return audioBlob;
  }, []);

  // 오디오 품질 확인
  const validateAudioQuality = useCallback((audioBlob) => {
    const minSize = 1000; // 최소 1KB
    const maxSize = 10 * 1024 * 1024; // 최대 10MB

    if (audioBlob.size < minSize) {
      throw new Error('녹음된 오디오가 너무 짧습니다.');
    }

    if (audioBlob.size > maxSize) {
      throw new Error('녹음된 오디오가 너무 큽니다.');
    }

    return true;
  }, []);

  // 오디오 전처리
  const preprocessAudio = useCallback(async (audioBlob) => {
    try {
      setIsProcessing(true);

      // 1. 오디오 품질 검증
      validateAudioQuality(audioBlob);

      // 2. 형식 변환 (필요시)
      const processedBlob = convertToWebM(audioBlob);

      // 3. 메타데이터 추가
      const audioData = {
        blob: processedBlob,
        size: processedBlob.size,
        type: processedBlob.type,
        duration: await getAudioDuration(processedBlob),
        timestamp: new Date().toISOString()
      };

      return audioData;

    } catch (error) {
      console.error('오디오 전처리 실패:', error);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [validateAudioQuality, convertToWebM]);

  // 오디오 지속시간 계산
  const getAudioDuration = useCallback((audioBlob) => {
    return new Promise((resolve) => {
      const audio = new Audio();
      const url = URL.createObjectURL(audioBlob);
      
      audio.onloadedmetadata = () => {
        URL.revokeObjectURL(url);
        resolve(audio.duration);
      };
      
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        resolve(0); // 오류 시 0 반환
      };
      
      audio.src = url;
    });
  }, []);

  // TTS 오디오 재생
  const playTTSAudio = useCallback(async (audioBlob) => {
    try {
      setIsSpeaking(true);

      // 기존 오디오 정지
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }

      const audio = new Audio();
      const url = URL.createObjectURL(audioBlob);
      
      audio.src = url;
      setCurrentAudio(audio);

      // 재생 완료 이벤트
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setIsSpeaking(false);
        setCurrentAudio(null);
      };

      // 오류 처리
      audio.onerror = (error) => {
        console.error('오디오 재생 실패:', error);
        URL.revokeObjectURL(url);
        setIsSpeaking(false);
        setCurrentAudio(null);
      };

      await audio.play();

    } catch (error) {
      console.error('TTS 재생 실패:', error);
      setIsSpeaking(false);
      throw error;
    }
  }, [currentAudio]);

  // 오디오 재생 중지
  const stopAudio = useCallback(() => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setCurrentAudio(null);
    }
    setIsSpeaking(false);
  }, [currentAudio]);

  // Base64로 인코딩 (API 전송용)
  const blobToBase64 = useCallback((blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result.split(',')[1]; // "data:audio/webm;base64," 제거
        resolve(base64String);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }, []);

  // ArrayBuffer로 변환 (API 전송용)
  const blobToArrayBuffer = useCallback((blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsArrayBuffer(blob);
    });
  }, []);

  // 오디오 형식 정보 추출
  const getAudioInfo = useCallback((audioBlob) => {
    return {
      type: audioBlob.type,
      size: audioBlob.size,
      sizeKB: Math.round(audioBlob.size / 1024),
      isWebM: audioBlob.type.includes('webm'),
      isWAV: audioBlob.type.includes('wav'),
    };
  }, []);

  return {
    isProcessing,
    isSpeaking,
    preprocessAudio,
    playTTSAudio,
    stopAudio,
    blobToBase64,
    blobToArrayBuffer,
    getAudioInfo,
    getAudioDuration
  };
};