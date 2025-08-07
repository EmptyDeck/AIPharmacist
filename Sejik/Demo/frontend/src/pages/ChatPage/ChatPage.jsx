// ChatPage.jsx
import React, { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import * as S from "./ChatPage.style";
import { Send, FileUp, Mail, Mic, CircleUserRound } from "lucide-react";
import { postChat, postFiles } from "../../apis/apis";
import ReactMarkdown from "react-markdown";




import { useVoiceConversation } from "./hooks/useVoiceConversation"; // sejik

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

  const [uploadedFileId, setUploadedFileId] = useState(null); // 🆕 file_id 저장용
  const [isProcessing, setIsProcessing] = useState(false); // 🆕 중복 방지 플래그


  //seijk
  const [isAutoVoiceMode, setIsAutoVoiceMode] = useState(false);
  const { isRecording, toggleRecording } = useVoiceConversation({
    apiBaseUrl: "http://localhost:8001",
    autoStart: true,
    onUserMessage: (text) => {
      if (!text.trim()) return;
      const userMessage = {
        id: Date.now().toString(),
        type: "user",
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
    },
    onBotMessage: (text) => {
      if (!text.trim()) return;
      const botMessage = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        content: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    },
  });

  // 자동 음성 대화 토글 핸들러
  const handleToggleAutoVoice = () => {
    if (isAutoVoiceMode) {
      // 모드 끄기 => 녹음 종료
      if (isRecording) toggleRecording();
      setIsAutoVoiceMode(false);
    } else {
      // 모드 켜기 => 녹음 시작
      if (!isRecording) toggleRecording();
      setIsAutoVoiceMode(true);
    }
  };

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
  // 🆕 중복 실행 방지
  if (isProcessing || isLoading) {
    console.log("🛑 이미 처리 중입니다. 중복 실행 방지.");
    return;
  }
  
  console.log("🚨 handleSendMessage 호출됨!");
  console.log("inputMessage:", inputMessage, "medicalDocument:", medicalDocument, "selectedFile:", selectedFile);
  console.log("uploadedFileId:", uploadedFileId);
  
  setIsProcessing(true); // 🆕 처리 시작 플래그
  
  try {
    // 파일이 선택되었지만 아직 업로드 안된 경우 먼저 업로드
    if (selectedFile && !uploadedFileId) {
      console.log("🔄 선택된 파일을 먼저 업로드합니다...");
      
      try {
        setMessages((prev) => [...prev, {
          id: Date.now().toString(),
          type: "bot", 
          content: "📤 파일을 업로드하고 있습니다...",
          timestamp: new Date(),
        }]);
        
        const res = await postFiles(selectedFile);
        console.log("📤 파일 업로드 완료:", res);
        
        if (res.file_id) {
          setUploadedFileId(res.file_id);
          console.log("✅ 파일 ID 설정됨:", res.file_id);
          
          // 🆕 업로드 완료 후 메시지 전송 (파일 ID 포함)
          await sendMessageWithFileId(res.file_id);
          return;
        }
      } catch (error) {
        console.error("❌ 파일 업로드 실패:", error);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            type: "bot",
            content: "❌ 파일 업로드 중 오류가 발생했습니다.",
            isError: true,
            timestamp: new Date(),
          },
        ]);
        return;
      }
    }
    
    // 일반적인 경우 (파일 없거나 이미 업로드됨)
    await sendMessageWithFileId(uploadedFileId);
    
  } finally {
    setIsProcessing(false); // 🆕 처리 완료 플래그
  }
};

// 실제 메시지 전송 함수 분리
const sendMessageWithFileId = async (fileId) => {
  console.log("📨 sendMessageWithFileId 호출, fileId:", fileId);
  
  const hasTextInput = inputMessage.trim() || medicalDocument.trim();
  const hasFileToProcess = fileId;
  
  if (!hasTextInput && !hasFileToProcess) {
    console.log("❌ 전송할 내용이 없음. 중단.");
    return;
  }
  
  let contentToSend;
  if (hasTextInput) {
    contentToSend = inputMessage.trim() || medicalDocument.trim();
  } else if (hasFileToProcess) {
    contentToSend = "업로드된 파일에 대해 설명해주세요";
  }

  const userMessage = {
    id: Date.now().toString(),
    type: "user",
    content: contentToSend,
    document: medicalDocument,
    conditions: selectedConditions,
    medications: selectedMedications,
    file: selectedFile,
    fileId: fileId,
    timestamp: new Date(),
  };

  console.log("📨 전송할 메시지:", userMessage);
  setMessages((prev) => [...prev, userMessage]);
  setInputMessage("");
  setMedicalDocument("");
  setIsLoading(true);

  try {
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
    
    // 성공적으로 전송된 후에만 파일 정보 초기화
    setSelectedFile(null);
    setUploadedFileName("");
    setUploadedFileId(null);
    
  } catch(e) {
    console.error("❌ postChat 통신 에러:", e);
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
  }
};





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

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadedFileName(file.name);
    setSelectedFile(file);

    try {
      const res = await postFiles(file);
      console.log("파일 업로드 결과:", res);
      
      // file_id 저장
      if (res.file_id) {
        setUploadedFileId(res.file_id);
        console.log("파일 ID 저장됨:", res.file_id);
      }
      
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type: "bot",
          content: `✅ 파일이 성공적으로 업로드되었습니다: ${file.name}${res.ocr_result ? '\n\n📄 OCR 텍스트가 추출되었습니다. 이제 이 문서에 대해 질문하거나 전송 버튼을 눌러주세요!' : ''}`,
          timestamp: new Date(),
        },
      ]);
      
      // 🚫 여기서 handleSendMessage() 호출하지 않음!
      
    } catch (err) {
      console.error("파일 업로드 실패:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type: "bot",
          content: "❌ 파일 업로드 중 오류가 발생했습니다.",
          isError: true,
          timestamp: new Date(),
        },
      ]);
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
    }
  }, [searchParams]);
  useEffect(() => {
    const summary = messages
      .map((msg) => `${msg.type === "user" ? "user" : "AI"}: ${msg.content}`)
      .join("\n");

    sessionStorage.setItem("chatSummary", summary);
  }, [messages]);

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
          <button
            style={{
              margin: "10px",
              padding: "8px 12px",
              backgroundColor: isAutoVoiceMode ? "#4caf50" : "#ccc",
              color: isAutoVoiceMode ? "white" : "black",
              borderRadius: "4px",
              cursor: "pointer",
              border: "none",
            }}
          >
            {isAutoVoiceMode ? "음성 대화 중지" : "음성 대화 시작"}
          </button>

          {messages.map((message) => (
            <S.MessageBubble key={message.id} $isUser={message.type === "user"}>
              <S.MessageContent $isUser={message.type === "user"}>
                {message.type === "bot" ? (
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                ) : (
                  message.content
                )}
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
            {uploadedFileName && (
              <S.FileUpload> 
                📎 {uploadedFileName} 
                {uploadedFileId && <span style={{color: 'green'}}> ✅</span>}
              </S.FileUpload>
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
                <Mic
                  style={{ cursor: "pointer" }}
                  onClick={handleToggleAutoVoice}
                />
              </div>
            </S.InputWrapper>
              <S.SendButton 
                onClick={handleSendMessage} 
                disabled={isLoading || isProcessing} // 🆕 처리 중일 때 비활성화
              >
                <Send size={18} />
                {isProcessing ? "처리중..." : "전송"}
              </S.SendButton>

          </S.MessageInputContainer>
        </S.InputArea>
      </S.ChatContainer>
    </S.PageWrapper>
  );
}
