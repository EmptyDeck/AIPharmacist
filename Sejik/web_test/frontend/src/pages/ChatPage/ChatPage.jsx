// ChatPage.jsx
import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import * as S from "./ChatPage.style";

//추가
import { Send, FileUp, Mail, Mic, MicOff } from "lucide-react";  // MicOff 추가
import { useVoiceRecorder } from './hooks/useVoiceRecorder';
import { useAudioProcessor } from './hooks/useAudioProcessor';
import { useSpeechAPI } from './hooks/useSpeechAPI';
//

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

  // 음성 관련 상태들
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");
  const {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    forceStop,
    setOnRecordingComplete
  } = useVoiceRecorder();

  const {
    isProcessing,
    isSpeaking,
    preprocessAudio,
    playTTSAudio,
    stopAudio
  } = useAudioProcessor();
  const {
  processVoiceMessage,
  isAnyLoading  // STT/TTS/LLM 로딩 상태
  } = useSpeechAPI();  
  // -세직


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

  // 녹음 완료 콜백 설정 (useEffect로 한 번만)
  useEffect(() => {
  if (isVoiceMode) {
    if (isAnyLoading) {
      setVoiceStatus("음성을 처리 중입니다...");
    } else if (isRecording) {
      setVoiceStatus("듣고 있습니다...");
    } else if (isSpeaking) {
      setVoiceStatus("응답을 재생 중입니다...");
    } else {
      setVoiceStatus("음성 모드가 활성화되었습니다. 말씀해주세요.");
    }
  }
  }, [isVoiceMode, isAnyLoading, isRecording, isSpeaking]);  // 의존성: 상태 변화 시 업데이트
  
  useEffect(() => {
  setOnRecordingComplete(async (audioBlob) => {
    try {
      // 1. 오디오 전처리
      const processedAudio = await preprocessAudio(audioBlob);
      
      // 2. 전체 파이프라인 (STT → LLM → TTS)
      const result = await processVoiceMessage(processedAudio.blob, {
        conditions: selectedConditions,
        medications: selectedMedications,
      });
      
      if (result.success) {
        // UI 업데이트: 사용자 메시지와 봇 응답 추가
        const userMessage = {
          id: Date.now().toString(),
          type: "user",
          content: result.userText || "음성 입력",  // STT 결과가 없으면 대체 텍스트
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        
        const botMessage = {
          id: (Date.now() + 1).toString(),
          type: "bot",
          content: result.aiText || "응답을 생성할 수 없습니다.",  // LLM 결과가 없으면 대체
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, botMessage]);
        
        // 3. TTS 재생
        await playTTSAudio(result.audioBlob);
      } else {
        setVoiceStatus(`음성 처리 실패: ${result.error || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("녹음 후 처리 실패:", error);
      setVoiceStatus("오류 발생: 다시 시도해주세요.");
    } finally {
      // 다음 녹음 준비
      if (isVoiceMode && !isAnyLoading) {  // 로딩 중이 아니면 재시작
        startRecording();
      }
    }
  });
  }, [setOnRecordingComplete, preprocessAudio, processVoiceMessage, playTTSAudio, isVoiceMode, selectedConditions, selectedMedications]);

  const handleVoiceToggle = async () => {
  if (!isVoiceMode) {
    try {
      const success = await startRecording();
      if (success) {
        setIsVoiceMode(true);
        // voiceStatus는 위 useEffect에서 자동 업데이트됨
      } else {
        setVoiceStatus("마이크 권한이 필요하거나 시작에 실패했습니다.");
      }
    } catch (error) {
      console.error("음성 모드 시작 실패:", error);
      setVoiceStatus("마이크 권한이 필요합니다. 브라우저 설정을 확인하세요.");
    }
  } else {
    forceStop();
    stopAudio();
    setIsVoiceMode(false);
    setVoiceStatus("");  // 즉시 초기화
    }
  };
  //////// 세직



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

  return (
    <S.PageWrapper>
      <S.Header>
        Dr. Watson
        <Link to={`/mail`}>
          <div title="대화 내용 메일로 전송">
            <Mail style={{ cursor: "pointer" }} />
          </div>
        </Link>
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
          {isAnyLoading && <S.Loading>음성 처리 중...</S.Loading>}

          {/* 음성 상태 표시 세직 */}
          {voiceStatus && (
            <S.VoiceStatusMessage>
              {voiceStatus}
            </S.VoiceStatusMessage>
          )}

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
                placeholder={isVoiceMode ? "음성 모드 활성화됨" : "질문을 입력하세요..."}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                disabled={isLoading || isVoiceMode}
              />
              
              {/* 음성 토글 버튼 */}
              <div 
                title={isVoiceMode ? "음성 모드 끄기" : "음성 모드 켜기"}
                onClick={handleVoiceToggle}
                style={{ 
                  cursor: "pointer",
                  color: isVoiceMode ? "#ff4444" : "#666",
                  display: "flex",
                  alignItems: "center",
                  padding: "4px"
                }}
              >
                {isVoiceMode ? (
                  <MicOff size={20} />  // 이제 import되어서 정상 작동
                ) : (
                  <Mic size={20} />
                )}
                {isRecording && (
                  <div style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "#ff4444",
                    marginLeft: "4px",
                    animation: "pulse 1s infinite"
                  }} />
                )}
              </div>
            </S.InputWrapper>
            <S.SendButton onClick={handleSendMessage} disabled={isLoading || isVoiceMode}>
              <Send size={18} />
              전송
            </S.SendButton>
          </S.MessageInputContainer>
        </S.InputArea>
      </S.ChatContainer>
    </S.PageWrapper>
  );
}
