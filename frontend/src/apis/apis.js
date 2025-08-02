import { jsonAxios } from "../axios";

// 채팅 생성
export const postChat = async (userMessage) => {
  const response = await jsonAxios.get(`/api/chat`, {
    request: userMessage.text, 
    currentMedications: userMessage.medications || [],
    underlying_diseases: userMessage.diseases || [],
  });
  console.log("BASE URL:", jsonAxios.defaults.baseURL);
  return response;
};

// 채팅 서비스 상태 조회
export const getHealth = async () => {
  const response = await jsonAxios.get(`/api/health`);
  return response;
};

// 네이버 로그인 조회
export const getLogin = async () => {
  const response = await jsonAxios.get(`/auth/login`);
  return response;
};

// 네이버 로그인 콜백
export const getCallback = async () => {
  const response = await jsonAxios.get(`/auth/callback`);
  return response;
};

// 이메일 단수 생성
export const postEmail = async () => {
  const response = await jsonAxios.get(`/api/send`);
  return response;
};

// 이메일 복수 생성
export const postEmails = async () => {
  const response = await jsonAxios.get(`/api/send-bulk`);
  return response;
};

// 이메일 조회
export const getEmail = async () => {
  const response = await jsonAxios.get(`/api/test`);
  return response;
};

// 디폴트 상태
export const getDefault = async () => {
  const response = await jsonAxios.get(`/`);
  return response;
};
