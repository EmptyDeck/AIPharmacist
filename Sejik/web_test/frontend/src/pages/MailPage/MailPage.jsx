import React, { useState } from "react";
import * as S from "./MailPage.style";
import { LogOut } from "lucide-react";
import { Link } from "react-router-dom";
export default function MailPage() {
  const [email, setEmail] = useState("");
  const [summary, setSummary] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    // 여기에 이메일 전송 로직 추가
    alert(`이메일 전송: ${email}\n요약 내용:\n${summary}`);
  };

  return (
    <>
      <S.Header>
        Dr. Watson
        <Link to={`/`}>
          <div title="챗으로 돌아가기">
            <LogOut style={{ cursor: "pointer" }} />
          </div>
        </Link>
      </S.Header>
      <S.Container>
        <S.SummaryBox>
          <h3>🧠 대화 요약</h3>
          <pre>{summary}</pre>
        </S.SummaryBox>
        <S.EmailForm onSubmit={handleSubmit}>
          <S.EmailInput
            type="email"
            placeholder="이메일 주소를 입력하세요"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <S.SendButton type="submit">보내기</S.SendButton>
        </S.EmailForm>
      </S.Container>
    </>
  );
}
