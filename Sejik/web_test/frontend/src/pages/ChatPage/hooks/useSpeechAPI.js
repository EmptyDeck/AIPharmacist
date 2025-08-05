// hooks/useSpeechAPI.js
import { useState, useCallback } from 'react';

// IBM Watson API 설정
const STT_CONFIG = {
  apiKey: 'lkDU8YLMlsM151S0B4gPGoYOg10KMm1GVeQl9u_zKqO0',
  url: 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/2a088970-da1a-4ff1-b35e-988423300d08',
  model: 'ko-KR_BroadbandModel'
};

const TTS_CONFIG = {
  apiKey: 'HdyjTuGXQOK8xoBfZARtvdaqOeEbZoLLad2FLCKCc2Jx',
  url: 'https://api.us-south.text-to-speech.watson.cloud.ibm.com/instances/5421e28b-1e74-4f93-9c05-808dcd0b7ca7',
  voice: 'ko-KR_JinV3Voice'
};

export const useSpeechAPI = () => {
  const [isSTTLoading, setIsSTTLoading] = useState(false);
  const [isTTSLoading, setIsTTSLoading] = useState(false);
  const [isLLMLoading, setIsLLMLoading] = useState(false);

  // STT: 음성 → 텍스트
  const speechToText = useCallback(async (audioBlob) => {
    try {
      setIsSTTLoading(true);

      // Basic Auth 헤더 생성
      const auth = btoa(`apikey:${STT_CONFIG.apiKey}`);
      
      const response = await fetch(
        `${STT_CONFIG.url}/v1/recognize?model=${STT_CONFIG.model}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': audioBlob.type || 'audio/webm',
            'Accept': 'application/json',
            'Authorization': `Basic ${auth}`
          },
          body: audioBlob
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`STT API 오류 (${response.status}): ${errorText}`);
      }

      const result = await response.json();
      console.log('STT 응답:', result);

      // 결과 파싱
      const results = result.results || [];
      if (results.length === 0 || !results[0].alternatives) {
        throw new Error('음성을 인식할 수 없습니다.');
      }

      const transcript = results[0].alternatives[0].transcript;
      const confidence = results[0].alternatives[0].confidence || 0;

      return {
        text: transcript.trim(),
        confidence: confidence,
        success: true
      };

    } catch (error) {
      console.error('STT 실패:', error);
      return {
        text: '',
        confidence: 0,
        success: false,
        error: error.message
      };
    } finally {
      setIsSTTLoading(false);
    }
  }, []);

  // TTS: 텍스트 → 음성
  const textToSpeech = useCallback(async (text) => {
    try {
      setIsTTSLoading(true);

      if (!text || text.trim().length === 0) {
        throw new Error('변환할 텍스트가 없습니다.');
      }

      // Basic Auth 헤더 생성
      const auth = btoa(`apikey:${TTS_CONFIG.apiKey}`);

      const response = await fetch(
        `${TTS_CONFIG.url}/v1/synthesize?voice=${TTS_CONFIG.voice}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'audio/webm',
            'Authorization': `Basic ${auth}`
          },
          body: JSON.stringify({
            text: text.trim()
          })
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`TTS API 오류 (${response.status}): ${errorText}`);
      }

      const audioBlob = await response.blob();
      console.log('TTS 성공, 오디오 크기:', audioBlob.size);

      return {
        audioBlob: audioBlob,
        success: true
      };

    } catch (error) {
      console.error('TTS 실패:', error);
      return {
        audioBlob: null,
        success: false,
        error: error.message
      };
    } finally {
      setIsTTSLoading(false);
    }
  }, []);

  // LLM: 텍스트 → AI 응답 (기존 postChat API 사용)
  const processWithLLM = useCallback(async (userText, messageContext) => {
    try {
      setIsLLMLoading(true);

      // 기존 postChat API 사용
      const { postChat } = await import('../../apis/apis');
      
      const userMessage = {
        id: Date.now().toString(),
        type: "user",
        content: userText,
        document: messageContext?.document || "",
        conditions: messageContext?.conditions || [],
        medications: messageContext?.medications || [],
        file: messageContext?.file || null,
        timestamp: new Date(),
      };

      console.log('LLM 요청:', userMessage);
      const response = await postChat(userMessage);
      
      return {
        text: response.answer || '응답을 생성할 수 없습니다.',
        confidence: response.model_metadata?.confidence || 0,
        success: true
      };

    } catch (error) {
      console.error('LLM 처리 실패:', error);
      return {
        text: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.',
        confidence: 0,
        success: false,
        error: error.message
      };
    } finally {
      setIsLLMLoading(false);
    }
  }, []);

  // 전체 파이프라인: STT → LLM → TTS
  const processVoiceMessage = useCallback(async (audioBlob, messageContext) => {
    try {
      console.log('음성 메시지 처리 시작');

      // 1. STT: 음성 → 텍스트
      const sttResult = await speechToText(audioBlob);
      if (!sttResult.success) {
        throw new Error(`음성 인식 실패: ${sttResult.error}`);
      }

      console.log('STT 완료:', sttResult.text);

      // 2. LLM: 텍스트 → AI 응답
      const llmResult = await processWithLLM(sttResult.text, messageContext);
      if (!llmResult.success) {
        throw new Error(`AI 응답 생성 실패: ${llmResult.error}`);
      }

      console.log('LLM 완료:', llmResult.text);

      // 3. TTS: AI 응답 → 음성
      const ttsResult = await textToSpeech(llmResult.text);
      if (!ttsResult.success) {
        throw new Error(`음성 합성 실패: ${ttsResult.error}`);
      }

      console.log('TTS 완료');

      return {
        userText: sttResult.text,
        aiText: llmResult.text,
        audioBlob: ttsResult.audioBlob,
        sttConfidence: sttResult.confidence,
        llmConfidence: llmResult.confidence,
        success: true
      };

    } catch (error) {
      console.error('음성 메시지 처리 실패:', error);
      return {
        userText: '',
        aiText: error.message,
        audioBlob: null,
        success: false,
        error: error.message
      };
    }
  }, [speechToText, processWithLLM, textToSpeech]);

  // API 상태 체크
  const checkAPIHealth = useCallback(async () => {
    try {
      // STT 서비스 체크
      const sttResponse = await fetch(`${STT_CONFIG.url}/v1/models`);
      const sttHealth = sttResponse.ok;

      // TTS 서비스 체크
      const ttsResponse = await fetch(`${TTS_CONFIG.url}/v1/voices`);
      const ttsHealth = ttsResponse.ok;

      return {
        stt: sttHealth,
        tts: ttsHealth,
        overall: sttHealth && ttsHealth
      };
    } catch (error) {
      console.error('API 상태 체크 실패:', error);
      return {
        stt: false,
        tts: false,
        overall: false
      };
    }
  }, []);

  return {
    // 개별 API 함수들
    speechToText,
    textToSpeech,
    processWithLLM,
    
    // 전체 파이프라인
    processVoiceMessage,
    
    // 로딩 상태들
    isSTTLoading,
    isTTSLoading,
    isLLMLoading,
    isAnyLoading: isSTTLoading || isTTSLoading || isLLMLoading,
    
    // 유틸리티
    checkAPIHealth
  };
};