
from pydantic import BaseModel, Field
from typing import List, Optional

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
    
    currentMedications: Optional[List[str]] = Field(
        default=None,
        description="현재 복용 중인 약물 목록 (선택사항). null 또는 빈 배열도 허용됩니다.",
        example=["아스피린", "메트포르민"]
    )

    # api 사용설명서
    class Config:
        json_schema_extra = {
            "example": {
                "question": "머리가 아파요. 어떻게 해야 할까요?",
                "underlying_diseases": ["고혈압"],
                "currentMedications": ["아스피린"]
            }
        }
