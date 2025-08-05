import { jsonAxios, formDataAxios } from "../axios";

// 채팅 생성
export const postChat = async (userMessage) => {
  const response = await jsonAxios.post(`/api/chat`, {
    question: userMessage.content,
    underlying_diseases: userMessage.conditions || [],
    currentMedications: userMessage.medications || [],
  });
  console.log("BASE URL:", jsonAxios.defaults.baseURL);
  return response.data;
};

// 구글 로그인 조회
export const getLogin = async () => {
  const response = await jsonAxios.get(`/auth/google/login-enhanced`);
  return response;
};

// 구글 로그인 콜백
export const getCallback = async () => {
  const response = await jsonAxios.get(`/auth/google/callback-enhanced`);
  return response;
};

// 이메일 단수 생성
export const postEmail = async (data) => {
  const response = await jsonAxios.post(`/api/send`, data);
  return response;
};

// 파일 업로드
export const postFiles = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await formDataAxios.post(`/api/files/upload`, formData, {});
  return response.data;
};
