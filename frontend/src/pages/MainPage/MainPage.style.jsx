import styled from "styled-components";
import bgImage from "../../images/blurry-gradient-haikei.svg";

export const MainContainer = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  margin: 0;
  padding: 180px 0 30px 40px;
`;

export const MainTitle1 = styled.h1`
  font-size: 60px;
  font-weight: 800;
  line-height: normal;
  color: #0b62fe;
  margin: 0;
`;
export const MainTitle2 = styled.h1`
  font-size: 40px;
  font-weight: 800;
  line-height: normal;
  color: #2b2b2b;
  margin: 0;
`;
export const MainImg = styled.div`
  background-image: url(${bgImage});
  background-size: cover;
  background-position: center;
  width: inherit;
  height: 100vh;
  display: flex;
`;
export const IntroContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 2rem;
  background-color: #fff;
  font-family: "Noto Sans KR", sans-serif;
  text-align: center;
`;
export const IntroContainer2 = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  background-color: #fff;
  font-family: "Noto Sans KR", sans-serif;
  text-align: center;
`;
export const IntroContainer3 = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 40vh;
  background-color: #fff;
  font-family: "Noto Sans KR", sans-serif;
  text-align: center;
`;
export const IntroBox = styled.div`
  display: flex;
  font-size: 20px;
  align-items: center;
  justify-content: center;
  font-weight: bold;
`;
export const SendButton = styled.button`
  margin: 40px auto;
  padding: 12px 16px;
  background-color: white;
  border: 2px solid #0b62fe;
  border-radius: 8px;
  font-weight: bold;
  display: block;
  cursor: pointer;
  text-align: center;

  a {
    color: #0b62fe;
    text-decoration: none;
    display: inline-block;
    width: 100%;
  }

  &:hover {
    background: #0b62fe;
    color: white;

    a {
      color: white;
    }
  }
`;

export const TitleBox = styled.div`
  display: inline-block;
  border: 2px solid #dbd6d6ff;
  border-radius: 12px;
  padding: 14px 20px;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #333;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: #b4b4b4;
  }
`;
export const TitleContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 12px;
  padding: 12px 0;
`;
export const FeatureGrid = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  margin-top: 32px;
`;

export const FeatureCard = styled.div`
  background: #f9fbff;
  border-radius: 12px;
  border: 1px solid #ccc;
  padding: 24px;
  width: 300px;
  color: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  text-align: left;
  font-size: 16px;
  line-height: 1.6;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: #b4b4b4;
  }
`;

export const SpecialReasonContainer = styled.div`
  width: 100%;
  margin: 40px auto;
  padding: 30px 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 18px rgba(14, 52, 110, 0.1);
  font-family: "Noto Sans KR", sans-serif;
  color: #1a2e6e;
  text-align: left;
  line-height: 1.8;
  display: flex;
  gap: 20px;
  justify-content: center;
`;

export const SpecialReasonTitle = styled.h3`
  font-size: 28px;
  font-weight: 900;
  margin-bottom: 16px;
  color: #0b4db1;
  padding-left: 12px;
`;

export const SpecialReasonList = styled.ul`
  list-style: none;
  padding-left: 0;
  margin: 0;
`;

export const SpecialReasonItem = styled.li`
  margin-bottom: 14px;
  font-size: 18px;
  position: relative;
  padding-left: 30px;
  font-weight: 600;

  &:before {
    content: "✔";
    position: absolute;
    left: 0;
    top: 2px;
    color: #0b62fe;
    font-weight: bold;
  }
`;
