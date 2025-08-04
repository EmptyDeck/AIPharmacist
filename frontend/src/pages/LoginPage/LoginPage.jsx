import React from "react";
import * as S from "./LoginPage.style";
import { getLogin, getCallback } from "../../apis/apis";

export default function LoginPage() {
  const handleLogin = async () => {
    try {
      const res = await getLogin();
      const { auth_url } = res.data;
      window.location.href = auth_url;
    } catch (error) {
      console.error("네이버 로그인 URL 호출 실패", error);
      alert("로그인 URL을 불러오지 못했습니다.");
    }
  };

  return (
    <S.Container>
      <S.Card>
        <S.Title>Dr. Watson</S.Title>
        <S.Subtitle>문구는 생각중</S.Subtitle>
        <S.LoginButton onClick={handleLogin}>
          <S.NaverLogo>N</S.NaverLogo>
          네이버로 로그인
        </S.LoginButton>
      </S.Card>
    </S.Container>
  );
}
