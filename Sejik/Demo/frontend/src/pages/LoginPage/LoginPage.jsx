import React from "react";
import * as S from "./LoginPage.style";
import { getLogin, getCallback } from "../../apis/apis";

export default function LoginPage() {
  const handleLogin = async () => {
    try {
      const res = await getLogin();
      const auth_url =
        typeof res === "string"
          ? res
          : res?.authorization_url || res?.data?.authorization_url;

      if (!auth_url) {
        alert("auth_url이 없습니다.");
        return;
      }

      window.location.href = auth_url;
    } catch (err) {
      console.error("getLogin 에러 발생:", err);
      alert("로그인 중 에러 발생");
    }
  };

  return (
    <S.Container>
      <S.Card>
        <S.Title>Dr. Watson</S.Title>
        <S.Subtitle>당신의 복약 도우미이자 건강 파트너</S.Subtitle>
        <S.LoginButton onClick={handleLogin}>
          <S.NaverLogo>G</S.NaverLogo>
          구글로 로그인
        </S.LoginButton>
      </S.Card>
    </S.Container>
  );
}
