// ChatPage.jsx
import React, { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import * as S from "./ChatPage.style";
import { Send, FileUp, Mail, Mic, CircleUserRound } from "lucide-react";
import { postChat, getHealth, getLogin, getCallback } from "../../apis/apis";
const commonConditions = [
  "당뇨병",
  "고혈압",
  "심장질환",
  "천식",
  "관절염",
  "갑상선질환",
  "고지혈증",
  "우울증",
  "불안장애",
  "만성폐쇄성폐질환",
];

const commonMedications = [
  "아스피린",
  "타이레놀",
  "부루펜",
  "메트포르민",
  "암로디핀",
  "아토르바스타틴",
  "오메프라졸",
  "레보티록신",
  "리시노프릴",
  "메트프롤롤",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [medicalDocument, setMedicalDocument] = useState("");
  const [selectedConditions, setSelectedConditions] = useState([]);
  const [selectedMedications, setSelectedMedications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDocumentInput, setShowDocumentInput] = useState(false);
  const [showFeedback, setShowFeedback] = useState({});
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchParams] = useSearchParams();
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setMessages([
      {
        id: "welcome",
        type: "bot",
        content:
          "안녕하세요! Dr. Watson입니다. 😊\n\n의사 소견서나 처방전에 대해 궁금한 점이 있으시면 편하게 물어보세요.",
        timestamp: new Date(),
      },
    ]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !medicalDocument.trim() && !selectedFile)
      return;
    const contentToSend =
      inputMessage.trim() ||
      medicalDocument.trim() ||
      (selectedFile ? uploadedFileName : "");

    const userMessage = {
      id: Date.now().toString(),
      type: "user",
      content: contentToSend,
      document: medicalDocument,
      conditions: selectedConditions,
      medications: selectedMedications,
      file: selectedFile,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      console.log("보낼 메시지:", userMessage);
      const response = await postChat(userMessage);
      const botMessage = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        content: response.answer,
        confidence: response.model_metadata?.confidence,
        warnings: [],
        interactions: [],
        references: [],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          type: "bot",
          content: "죄송합니다. 오류가 발생했습니다.",
          isError: true,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
      setUploadedFileName("");
    }
  };

  /*const simulateAPICall = async (message) => {
    await new Promise((r) => setTimeout(r, 1000));
    if (
      message.content.includes("당뇨") ||
      message.medications.includes("메트포르민")
    ) {
      return {
        answer: "당뇨병 관련 정보입니다.",
        confidence_score: 0.95,
        safety_warnings: [],
        drug_interactions: [],
        references: [],
      };
    }
    return {
      answer: "해당 정보를 찾을 수 없습니다.",
      confidence_score: 0.6,
      safety_warnings: ["개인차가 있으므로 전문가 상담 필요"],
      drug_interactions: [],
      references: [],
    };
  };*/

  const toggleCondition = (condition) => {
    setSelectedConditions((prev) =>
      prev.includes(condition)
        ? prev.filter((c) => c !== condition)
        : [...prev, condition]
    );
  };

  const toggleMedication = (medication) => {
    setSelectedMedications((prev) =>
      prev.includes(medication)
        ? prev.filter((m) => m !== medication)
        : [...prev, medication]
    );
  };
  const handleFileButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFileName(file.name);
      setSelectedFile(file);
    }
  };
  useEffect(() => {
    const authSuccess = searchParams.get("auth_success");
    const id = searchParams.get("user_id");
    const name = searchParams.get("user_name");

    if (authSuccess === "true" && id) {
      setUserId(id);
      setUserName(name);
      setIsAuthenticated(true);
      // 필요하면 로컬스토리지 등에도 저장
      // localStorage.setItem('userId', id);
      // localStorage.setItem('userName', name);
    }
  }, [searchParams]);

  return (
    <S.PageWrapper>
      <S.Header>
        Dr. Watson
        <S.IconBox>
          <Link to={`/mail`}>
            <div title="대화 내용 메일로 전송">
              <Mail style={{ cursor: "pointer" }} />
            </div>
          </Link>
          <Link to={`/login`}>
            <CircleUserRound />
          </Link>
        </S.IconBox>
      </S.Header>

      <S.ChatContainer>
        <S.MessageList>
          {messages.map((message) => (
            <S.MessageBubble key={message.id} $isUser={message.type === "user"}>
              <S.MessageContent $isUser={message.type === "user"}>
                {message.content}
              </S.MessageContent>
              <S.Timestamp $isUser={message.type === "user"}>
                {message.timestamp.toLocaleTimeString()}
              </S.Timestamp>
            </S.MessageBubble>
          ))}
          {isLoading && <S.Loading>답변 생성 중...</S.Loading>}
          <div ref={messagesEndRef} />
        </S.MessageList>

        <S.InputArea>
          <S.SelectContainer>
            <label>기저질환 선택</label>
            <div>
              {commonConditions.map((c) => (
                <S.SelectButton
                  key={c}
                  selected={selectedConditions.includes(c)}
                  onClick={() => toggleCondition(c)}
                >
                  {c}
                </S.SelectButton>
              ))}
            </div>
          </S.SelectContainer>

          <S.SelectContainer>
            <label>복용약물 선택</label>
            <div>
              {commonMedications.map((m) => (
                <S.SelectButton
                  key={m}
                  selected={selectedMedications.includes(m)}
                  onClick={() => toggleMedication(m)}
                >
                  {m}
                </S.SelectButton>
              ))}
            </div>
          </S.SelectContainer>
          {uploadedFileName && <S.FileUpload> {uploadedFileName}</S.FileUpload>}
          {showDocumentInput && (
            <S.TextArea
              placeholder="의료 문서를 입력하세요..."
              value={medicalDocument}
              onChange={(e) => setMedicalDocument(e.target.value)}
            />
          )}

          <S.MessageInputContainer>
            <S.SendButton>
              <FileUp size={18} onClick={handleFileButtonClick} />
            </S.SendButton>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <S.InputWrapper>
              <S.Input
                placeholder="질문을 입력하세요..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                disabled={isLoading}
              />
              <div title="음성 입력">
                <Mic style={{ cursor: "pointer" }} />
              </div>
            </S.InputWrapper>
            <S.SendButton onClick={handleSendMessage} disabled={isLoading}>
              <Send size={18} />
              전송
            </S.SendButton>
          </S.MessageInputContainer>
        </S.InputArea>
      </S.ChatContainer>
    </S.PageWrapper>
  );
}
