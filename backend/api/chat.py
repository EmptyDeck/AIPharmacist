
import httpx
from fastapi import APIRouter, HTTPException
from schemas.chat import ChatRequest
from core.config import settings
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
import asyncio
from typing import Optional

# AI 에이전트 임포트
from api.chatbot.explainAI import explain_ai
from api.chatbot.warnAI import warn_ai
from api.chatbot.calendarAI import calendar_ai
import uuid

# APIRouter 인스턴스 생성
router = APIRouter()

# IBM Watson 모델 인스턴스 (전역으로 한 번만 초기화)
_watson_model: Optional[Model] = None


def get_watson_model() -> Model:
    """IBM Watson 모델 인스턴스를 반환합니다 (Singleton 패턴)"""
    global _watson_model
    if _watson_model is None:
        # 설정 검증
        if not settings.WATSONX_API_KEY or not settings.WATSONX_PROJECT_ID:
            raise HTTPException(
                status_code=500,
                detail="IBM Watson API 키 또는 프로젝트 ID가 설정되지 않았습니다."
            )

        try:
            # IBM Watson 자격 증명 설정
            creds = {
                "url": settings.WATSONX_API_URL,
                "apikey": settings.WATSONX_API_KEY
            }

            # 모델 인스턴스 생성
            _watson_model = Model(
                model_id='ibm/granite-3-3-8b-instruct',
                credentials=creds,
                project_id=settings.WATSONX_PROJECT_ID
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"IBM Watson 모델 초기화 실패: {str(e)}"
            )
    return _watson_model


def get_medical_completion(prompt: str) -> str:
    """IBM Watson 모델에게 의료 상담 요청을 보내고 응답을 반환합니다"""
    try:
        model = get_watson_model()
        response = model.generate(
            prompt=prompt,
            params={
                GenParams.MAX_NEW_TOKENS: 300,  # 의료 상담용으로 조금 더 길게
                GenParams.TEMPERATURE: 0.3,     # 의료 정보는 보수적으로
                GenParams.REPETITION_PENALTY: 1.1
            }
        )
        return response['results'][0]['generated_text']
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"IBM Watson 모델 오류: {str(e)}")


def classify_user_input(query: str) -> str:
    """사용자 입력을 분류하여 적절한 AI 에이전트를 선택합니다"""
    query_lower = query.lower()
    
    # 경고/부작용 관련 키워드
    warn_keywords = [
        '부작용', '위험', '주의', '경고', '안전', '금기', '독성', '과량',
        '응급', '알레르기', '상호작용', '임신', '수유', '간독성', '신독성'
    ]
    
    # 약물 설명 관련 키워드  
    explain_keywords = [
        '효과', '효능', '작용', '성분', '원리', '어떻게', '왜', '설명',
        '무엇', '약', '성분', '기전', '치료', '개선', '완화'
    ]
    
    # 캘린더 관련 키워드
    calendar_keywords = [
        '일정', '캘린더', '알림', '스케줄', '추가', '등록', '복용',
        '먹어', '드세요', '아침', '점심', '저녁', '식전', '식후', '하루'
    ]
    
    # 우선순위: 캘린더 > 경고 > 설명 > 일반
    if any(keyword in query_lower for keyword in calendar_keywords):
        return "add_cal"
    elif any(keyword in query_lower for keyword in warn_keywords):
        return "warn"
    elif any(keyword in query_lower for keyword in explain_keywords):
        return "explain"
    else:
        return "general"


@router.post("/chat", summary="의료 AI 채팅")
async def get_chat_response(request: ChatRequest):
    """프론트엔드 요청을 적절한 AI 에이전트로 라우팅하여 응답을 반환합니다."""

    # 사용자 컨텍스트 구성
    user_context_dict = {
        'underlying_diseases': request.underlying_diseases,
        'currentMedications': request.currentMedications
    }
    
    user_context = []
    if request.underlying_diseases:
        user_context.append(f"기저질환: {', '.join(request.underlying_diseases)}")
    if request.currentMedications:
        user_context.append(
            f"현재 복용 약물: {', '.join(request.currentMedications)}")

    context_text = " | ".join(
        user_context) if user_context else "특별한 기저질환이나 복용 약물 없음"
    
    # 사용자 입력 분류
    agent_type = classify_user_input(request.question)
    
    # 세션 ID 생성 (캘린더 AI용)
    session_id = str(uuid.uuid4())

    # 의료 전용 프롬프트 구성
    medical_prompt = f"""
당신은 전문적인 의료 AI 어시스턴트입니다. 다음 지침을 따라 응답해주세요:

지침:
1. 정확하고 신뢰할 수 있는 의료 정보만 제공하세요
2. 응급상황이 의심되면 즉시 병원 방문을 권하세요
3. 진단이나 처방은 하지 말고, 일반적인 건강 조언만 제공하세요
4. 불확실한 정보는 "전문의와 상담하세요"라고 안내하세요
5. 따뜻하고 공감적인 톤으로 응답하세요

환자 정보:
- 사용자 상태: {context_text}
- 질문: "{request.question}"

위 정보를 바탕으로 적절한 의료 조언을 제공해주세요:
"""

    try:
        # AI 에이전트별 처리
        if agent_type == "explain":
            # 약물 설명 AI
            loop = asyncio.get_event_loop()
            agent_response = await loop.run_in_executor(
                None,
                explain_ai.explain_medication,
                request.question,
                user_context_dict
            )
            agent_name = "ExplainAI"
            
        elif agent_type == "warn":
            # 경고/안전 AI
            loop = asyncio.get_event_loop()
            agent_response = await loop.run_in_executor(
                None,
                warn_ai.check_safety_warnings,
                request.question,
                user_context_dict
            )
            agent_name = "WarnAI"
            
        elif agent_type == "add_cal":
            # 캘린더 AI
            loop = asyncio.get_event_loop()
            agent_response = await loop.run_in_executor(
                None,
                calendar_ai.handle_calendar_request,
                request.question,
                session_id,
                user_context_dict
            )
            agent_name = "CalendarAI"
            
        else:
            # 일반 의료 상담 (기존 로직)
            loop = asyncio.get_event_loop()
            agent_response = await loop.run_in_executor(
                None,
                get_medical_completion,
                medical_prompt
            )
            agent_name = "GeneralAI"

        # 성공 응답 반환
        return {
            "answer": agent_response.strip(),
            "user_context": {
                "underlying_diseases": request.underlying_diseases,
                "medications": request.currentMedications
            },
            "model_metadata": {
                "model_name": "IBM Granite 3.3 8B Instruct",
                "model_provider": "IBM Watson",
                "agent_used": agent_name,
                "agent_type": agent_type,
                "session_id": session_id if agent_type == "add_cal" else None,
                "context_provided": bool(user_context),
                "disclaimer": "이는 일반적인 건강 정보이며, 전문 의료진의 진료를 대체할 수 없습니다."
            },
            "status": "success"
        }

    except HTTPException:
        # Watson 모델 오류 시 기존 fallback 로직 사용
        raise
    except Exception as e:
        # 기타 예외 시 fallback 응답
        return await _get_fallback_response(request, f"서비스 일시 중단: {str(e)}")


async def _get_fallback_response(request: ChatRequest, error_msg: str):
    """AI 모델 연결 실패 시 기본 응답을 제공합니다."""

    user_context = []
    if request.underlying_diseases:
        user_context.append(f"기저질환: {', '.join(request.underlying_diseases)}")
    if request.currentMedications:
        user_context.append(f"복용약물: {', '.join(request.currentMedications)}")

    context_text = " | ".join(user_context) if user_context else "없음"

    fallback_response = f"""죄송합니다. 현재 AI 상담 서비스에 일시적인 문제가 발생했습니다.
오류: {error_msg}

귀하의 질문: "{request.question}"
사용자 정보: {context_text}

일반적인 건강 관리 조언:
- 증상이 지속되거나 악화되면 즉시 전문의와 상담하세요
- 응급상황이라고 판단되면 119에 신고하거나 응급실로 가세요
- 처방받은 약물은 의사의 지시에 따라 정확히 복용하세요
- 규칙적인 생활습관과 충분한 휴식을 취하세요

※ 이는 일반적인 건강 정보이며, 개인의 구체적인 상황에 맞는 전문적인 의료 상담을 대체할 수 없습니다."""

    return {
        "answer": fallback_response,
        "user_context": {
            "underlying_diseases": request.underlying_diseases,
            "medications": request.currentMedications
        },
        "status": "fallback",
        "error": error_msg
    }


@router.get("/health", summary="채팅 서비스 상태 확인")
async def health_check():
    """IBM Watson 모델 연결 상태를 확인합니다."""

    # IBM Watson 설정 상태 확인
    config_status = {
        "WATSONX_API_URL": bool(settings.WATSONX_API_URL),
        "WATSONX_API_KEY": bool(settings.WATSONX_API_KEY),
        "WATSONX_PROJECT_ID": bool(settings.WATSONX_PROJECT_ID)
    }

    # IBM Watson 모델 연결 테스트
    watson_status = "unknown"
    watson_error = None

    try:
        # Watson 모델 인스턴스 생성 테스트
        test_model = get_watson_model()
        if test_model:
            watson_status = "healthy"
        else:
            watson_status = "unavailable"
            watson_error = "Model instance creation failed"
    except Exception as e:
        watson_status = "error"
        watson_error = str(e)

    all_configured = all([
        settings.WATSONX_API_URL,
        settings.WATSONX_API_KEY,
        settings.WATSONX_PROJECT_ID
    ])

    overall_status = "healthy" if watson_status == "healthy" and all_configured else "degraded"

    return {
        "service": "Dr.Watson Chat API",
        "status": overall_status,
        "config_status": config_status,
        "watson_model_status": watson_status,
        "watson_error": watson_error,
        "all_configured": all_configured,
        "model_id": "ibm/granite-3-3-8b-instruct",
        "message": "IBM Watson 모델이 정상 작동 중입니다." if overall_status == "healthy" else "IBM Watson 설정을 확인하세요."
    }
