import React, { useState, useEffect } from "react";
import * as S from "./MailPage.style";
import { LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { postEmail } from "../../apis/apis";
export default function MailPage() {
  const [email, setEmail] = useState("");
  const [summary, setSummary] = useState("");
  const [patientName, setPatientName] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    // 여기에 이메일 전송 로직 추가
    const payload = {
      recipient: email,
      patient_name: patientName,
      chat_history: summary,
      doctor_name: "IBM_DoctorAI",
    };

    try {
      const res = await postEmail(payload);
      alert("이메일이 성공적으로 전송되었습니다!");
    } catch (err) {
      alert("이메일 전송에 실패했습니다.");
      console.error(err);
    }
  };
  useEffect(() => {
    const summaryFromStorage = sessionStorage.getItem("chatSummary");
    const userNameFromParams = new URLSearchParams(window.location.search).get(
      "user_name"
    );
    setSummary(summaryFromStorage || "");
    setPatientName(userNameFromParams || "");
  }, []);

  return (
    <>
      <S.Header>
        Dr. Watson
        <Link to={`/chat`}>
          <div title="챗으로 돌아가기">
            <LogOut style={{ cursor: "pointer" }} />
          </div>
        </Link>
      </S.Header>
      <S.Container>
        <S.SummaryBox>
          <h3>대화 요약</h3>
          <pre>{summary}</pre>
        </S.SummaryBox>
        <S.EmailForm onSubmit={handleSubmit}>
          <S.EmailInput
            type="name"
            placeholder="성함을 입력하세요"
            value={patientName}
            onChange={(e) => setPatientName(e.target.value)}
          />
          <S.EmailInput
            type="email"
            placeholder="이메일 주소를 입력하세요"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <S.SendButton type="submit">전송</S.SendButton>
        </S.EmailForm>
      </S.Container>
    </>
  );
}
