import { jsonAxios } from "../axios";

// 스마트 API 함수
const smartApiCall = async (endpoint, data = null, method = 'POST') => {
  const urls = [
    'http://localhost:8001',  // 개발환경
    '',                       // 배포환경 (상대경로)
  ];
  
  for (const baseURL of urls) {
    try {
      console.log(`시도 중: ${baseURL || '배포서버'}${endpoint}`);
      
      const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
      };
      
      // GET 요청이 아닐 때만 body 추가
      if (method !== 'GET' && data) {
        options.body = JSON.stringify(data);
      }
      
      const response = await fetch(`${baseURL}${endpoint}`, options);
      
      if (response.ok) {
        console.log(`✅ 성공: ${baseURL || '배포서버'}`);
        return await response.json();
      }
    } catch (error) {
      console.log(`❌ 실패: ${baseURL || '배포서버'}`);
      continue;
    }
  }
  
  throw new Error('모든 서버 연결 실패');
};

// 모든 API 함수들을 스마트 버전으로 교체
export const postChat = async (userMessage) => {
  return await smartApiCall('/api/chat', {
    question: userMessage.content,
    underlying_diseases: userMessage.conditions || [],
    currentMedications: userMessage.medications || [],
  });
};

export const getHealth = async () => {
  return await smartApiCall('/api/health', null, 'GET');
};

export const getLogin = async () => {
  return await smartApiCall('/auth/login', null, 'GET');
};

export const getCallback = async () => {
  return await smartApiCall('/auth/callback', null, 'GET');
};

export const postEmail = async () => {
  return await smartApiCall('/api/send', null, 'GET'); // 이것도 GET인가요?
};

export const postEmails = async () => {
  return await smartApiCall('/api/send-bulk', null, 'GET');
};

export const getEmail = async () => {
  return await smartApiCall('/api/test', null, 'GET');
};

export const getDefault = async () => {
  return await smartApiCall('/', null, 'GET');
};

