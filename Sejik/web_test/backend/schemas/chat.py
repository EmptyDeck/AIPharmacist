
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="사용자 질문")
    underlying_diseases: Optional[List[str]] = Field(None, description="기저질환 목록")
    currentMedications: Optional[List[str]] = Field(None, description="복용 약물 목록")