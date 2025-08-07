import styled from "styled-components";

export const Container = styled.div`
  height: 100vh;
  background-color: #f8f9fb;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
`;

export const Card = styled.div`
  background-color: #fff;
  padding: 48px 36px;
  border-radius: 16px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
  text-align: center;
  width: 360px;
`;

export const Title = styled.h1`
  font-size: 28px;
  color: #0b62fe;
  margin-bottom: 8px;
`;

export const Subtitle = styled.p`
  color: #555;
  font-size: 14px;
  margin-bottom: 32px;
`;

export const LoginButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
  color: black;
  border: 1px solid #dadada;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 8px;
  margin: 0 auto;
  &:hover {
    background-color: #f1f1f1;
  }
`;
export const NaverLogo = styled.span`
  font-weight: bold;
  color: #000;
  font-size: 20px;
  margin-right: 8px;
`;
