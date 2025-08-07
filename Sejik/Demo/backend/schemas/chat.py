# Sejik/Demo/backend/schemas/chat.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    """의료 AI 채팅 요청 모델"""
    
    question: str = Field(
        ..., 
        min_length=1, 
        description="사용자의 의료 관련 질문 (필수)",
        example="머리가 아파요. 어떻게 해야 할까요?"
    )
    
    underlying_diseases: Optional[List[str]] = Field(
        default=None,
        description="사용자의 기저질환 목록 (선택사항). null 또는 빈 배열도 허용됩니다.",
        example=["고혈압", "당뇨병"]
    )
    
    current_medications: Optional[List[str]] = Field(
        default=None,
        description="현재 복용 중인 약물 목록 (선택사항). null 또는 빈 배열도 허용됩니다.",
        example=["아스피린", "메트포르민"]
    )
    
    # 🆕 파일 ID 필드 추가
    file_id: Optional[str] = Field(
        default=None,
        description="업로드된 파일의 ID (선택사항). 이미지 분석이 필요한 경우 사용",
        example="123e4567-e89b-12d3-a456-426614174000"
    )

    # api 사용설명서
    class Config:
        json_schema_extra = {
            "example": {
                "question": "이 처방전에 대해 설명해주세요",
                "underlying_diseases": ["고혈압"],
                "current_medications": ["아스피린"],
                "file_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ChatResponse(BaseModel):
    """의료 AI 채팅 응답 모델 (템플릿 호환성)"""
    
    answer: str = Field(
        ..., 
        title="AI 모델의 답변", 
        description="AI 모델이 생성한 답변 내용입니다.",
        example="두통의 원인은 매우 다양합니다. 충분한 휴식을 취하고 수분을 섭취해보세요."
    )
    
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="사용자 컨텍스트 정보",
        example={
            "underlying_diseases": ["고혈압"],
            "medications": ["아스피린"]
        }
    )
    
    model_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="AI 모델 메타데이터",
        example={
            "model_name": "IBM Granite 3.3 8B Instruct",
            "agent_used": "GeneralAI"
        }
    )
    
    status: str = Field(
        default="success",
        description="응답 상태",
        example="success"
    )