// src/apis/apis.js
import smartApiCall from "./smartApi";

// 채팅 생성 - 🆕 file_id 지원 추가
export const postChat = async (userMessage) => {
  return await smartApiCall('/api/chat', {
    question: userMessage.content,
    underlying_diseases: userMessage.conditions || [],
    current_medications: userMessage.medications || [],
    file_id: userMessage.fileId || null, // 🆕 file_id 추가
  }, 'POST');
};

// 구글 로그인 조회
export const getLogin = async () => {
  return await smartApiCall('/auth/google/login-enhanced', null, 'GET');
};

// 구글 로그인 콜백
export const getCallback = async () => {
  return await smartApiCall('/auth/google/callback-enhanced', null, 'GET');
};

// 이메일 단수 생성
export const postEmail = async (data) => {
  return await smartApiCall('/api/send', data, 'POST');
};

// 파일 업로드 (FormData)
export const postFiles = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return await smartApiCall('/api/files/upload', formData, 'POST', true);
};