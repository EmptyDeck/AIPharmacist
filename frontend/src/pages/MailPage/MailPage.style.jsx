import styled, { css, keyframes } from "styled-components";
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
export const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  min-height: 100vh;
  padding: 60px 20px 20px;
  font-family: "Pretendard";
`;

export const SummaryBox = styled.div`
  background-color: #f9f9f9;
  border-left: 5px solid #0b62fe;
  margin-bottom: 20px;
  border-radius: 8px;
  width: 100%;
  max-width: 600px;
  padding: 24px;
`;

export const EmailForm = styled.form`
  display: flex;
  gap: 10px;
  align-items: center;
  width: 300px;
`;

export const EmailInput = styled.input`
  flex: 1;
  padding: 10px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
`;

export const SendButton = styled.button`
  background-color: #0b62fe;
  color: white;
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;

  &:hover {
    background-color: #084ed6;
  }
`;
