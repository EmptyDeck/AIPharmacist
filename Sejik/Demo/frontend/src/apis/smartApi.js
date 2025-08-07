// src/apis/smartApi.js

const smartApiCall = async (
  endpoint,
  data = null,
  method = 'POST',
  isFormData = false,
  isFileDownload = false
) => {
  const urls = [
    'http://localhost:8001', // 개발환경
    '' // 배포환경(상대경로)
  ];
  for (const baseURL of urls) {
    try {
      const url = `${baseURL}${endpoint}`;
      const options = { method, headers: {} };
      // FormData면 Content-Type 자동처리(생략)
      if (!isFormData) options.headers['Content-Type'] = 'application/json';
      if (method !== 'GET' && data) {
        options.body = isFormData ? data : JSON.stringify(data);
      }
      const response = await fetch(url, options);
      if (response.ok) {
        if (isFileDownload) return await response.blob();
        return await response.json();
      }
    } catch (e) {
      continue;
    }
  }
  throw new Error('모든 서버 연결 실패');
};
export default smartApiCall;
