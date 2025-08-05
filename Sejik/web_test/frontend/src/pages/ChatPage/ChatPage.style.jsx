import styled, { css, keyframes } from "styled-components";

export const PageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f9fafb;
`;

export const Header = styled.header`
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  font-size: 24px;
  font-weight: bold;
  color: #0b62fe;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
`;

export const ChatContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 24px;
  gap: 16px;
`;
const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const MessageList = styled.div`
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

export const MessageBubble = styled.div`
  display: flex;
  flex-direction: column;
  align-items: ${(props) => (props.$isUser ? "flex-end" : "flex-start")};
  animation: ${fadeInUp} 0.3s ease forwards;
`;

export const MessageContent = styled.div`
  background: ${({ $isUser }) => ($isUser ? "#3b82f6" : "#ffffff")};
  color: ${({ $isUser }) => ($isUser ? "white" : "#1f2937")};
  padding: 10px 14px;
  border-radius: 12px;
  max-width: 70%;
  font-size: 14px;
  white-space: pre-wrap;
`;

export const Timestamp = styled.div`
  margin-top: 4px;
  font-size: 10px;
  color: #6b7280;
  text-align: text-align: ${({ $isUser }) => ($isUser ? "right" : "left")};
`;

export const InputArea = styled.div`
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

export const SelectContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

export const SelectButton = styled.button`
  margin-right: 6px;
  margin-bottom: 6px;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 13px;
  border: none;
  cursor: pointer;
  ${({ selected }) =>
    selected
      ? css`
          background-color: #10b981;
          color: white;
        `
      : css`
          background-color: #f3f4f6;
          color: #374151;
          &:hover {
            background-color: #e5e7eb;
          }
        `}
`;

export const TextArea = styled.textarea`
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  resize: none;
  font-size: 14px;
`;

export const MessageInputContainer = styled.div`
  display: flex;
  gap: 8px;
  width: 100%;
`;
export const InputWrapper = styled.div`
  display: flex;
  align-items: center;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 12px;
  background-color: white;
  flex: 1;
`;
export const Input = styled.input`
  flex: 1;
  padding: 12px 0;
  border: none;
  font-size: 14px;
  background-color: transparent;

  &:focus {
    outline: none;
  }
`;

export const SendButton = styled.button`
  padding: 12px 16px;
  background-color: #3b82f6;
  color: white;
  font-weight: bold;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  &:disabled {
    background-color: #d1d5db;
    cursor: not-allowed;
  }
`;

export const Loading = styled.div`
  font-size: 14px;
  color: #6b7280;
`;

export const FileUpload = styled.div`
  display: inline-block;
  background-color: #e6f4f1;
  color: #2a8a6d;
  padding: 6px 12px;
  margin: 8px 4px 0 0;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 500;
  width: fit-content;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;






//세직
// 음성 상태 메시지 스타일
export const VoiceStatusMessage = styled.div`
  background: #e3f2fd;
  color: #1976d2;
  padding: 12px 16px;
  border-radius: 12px;
  margin: 8px 0;
  text-align: center;
  font-size: 14px;
  border: 1px solid #bbdefb;
  font-style: italic;
`;

// 펄스 애니메이션 추가 (전역 스타일이나 별도 CSS 파일에)
const pulseAnimation = `
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
`;