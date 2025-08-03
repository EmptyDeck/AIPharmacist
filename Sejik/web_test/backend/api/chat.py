import httpx
from fastapi import APIRouter, HTTPException
from schemas.chat import ChatRequest
from core.config import settings
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
import asyncio
from typing import Optional
from .chatbot.explainAI import ExplainAI
from .chatbot.warnAI import WarnAI
from .chatbot.calendarAI import CalendarAI


# APIRouter 인스턴스 생성
router = APIRouter()

# IBM Watson 모델 인스턴스 (전역으로 한 번만 초기화)
_watson_model: Optional[Model] = None

# 전문 AI 에이전트 인스턴스들
_explain_ai: Optional[ExplainAI] = None
_warn_ai: Optional[WarnAI] = None
_calendar_ai: Optional[CalendarAI] = None
_user_sessions = {}

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

def get_specialized_agents():
    """전문 AI 에이전트들을 초기화하고 반환합니다"""
    global _explain_ai, _warn_ai, _calendar_ai
    
    if _explain_ai is None:
        _explain_ai = ExplainAI()
    if _warn_ai is None:
        _warn_ai = WarnAI()
    if _calendar_ai is None:
        _calendar_ai = CalendarAI()
    
    return _explain_ai, _warn_ai, _calendar_ai

    
    return _explain_ai, _warn_ai

def classify_user_input(question: str) -> str:
    """사용자 입력을 간단히 분류 (키워드 기반)"""
    question_lower = question.lower()
    
    # 약물 경고 관련 키워드
    warn_keywords = ['부작용', '위험', '주의사항', '금기', '안전', '위험성', '조심', '문제']
    if any(keyword in question_lower for keyword in warn_keywords):
        return "warn"
    
    # 약물 설명 관련 키워드  
    explain_keywords = ['효능', '성분', '복용법', '작용', '원리', '어떤', '무엇', '설명', '정보']
    drug_names = ['타이레놀', '아스피린', '이부프로펜', '약', '의약품', '처방약']
    if (any(keyword in question_lower for keyword in explain_keywords) and 
        any(drug in question_lower for drug in drug_names)) or any(drug in question_lower for drug in drug_names):
        return "explain"
    
    # 캘린더 관련 키워드
    calendar_keywords = ['일정', '알림', '스케줄', '캘린더', '복용 시간', '시간 설정']
    if any(keyword in question_lower for keyword in calendar_keywords):
        return "add_cal"
    
    # 기본값은 일반 대화
    return "general"

def get_medical_completion(prompt: str) -> str:
    """IBM Watson 모델에게 의료 상담 요청을 보내고 응답을 반환합니다"""
    try:
        model = get_watson_model()
        response = model.generate(
            prompt=prompt,
            params={
                GenParams.MAX_NEW_TOKENS: 300,
                GenParams.TEMPERATURE: 0.3,
                GenParams.REPETITION_PENALTY: 1.1
            }
        )
        return response['results'][0]['generated_text']
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"IBM Watson 모델 오류: {str(e)}")

@router.post("/chat", summary="의료 AI 채팅")
async def get_chat_response(request: ChatRequest):
    """
    메인 채팅 엔드포인트
    - 일반 대화는 직접 처리
    - 특정 정보는 전문 AI로 라우팅
    """
    
    try:
        # 사용자 컨텍스트 구성
        user_context = []
        if request.underlying_diseases:
            user_context.append(f"기저질환: {', '.join(request.underlying_diseases)}")
        if request.currentMedications:
            user_context.append(f"현재 복용 약물: {', '.join(request.currentMedications)}")

        context_text = " | ".join(user_context) if user_context else "특별한 기저질환이나 복용 약물 없음"
        
        # 1단계: 간단한 키워드 기반 분류
        classification = classify_user_input(request.question)
        print(f"[INFO] 분류 결과: {classification}")
        
        agent_used = "MainChat"
        ai_response = ""
        loop = asyncio.get_event_loop()
        
        if classification == "explain":
            # 약물 설명 AI 호출
            print("[INFO] ExplainAI 호출 중...")
            explain_ai, _ = get_specialized_agents()
            agent_used = "ExplainAI"
            ai_response = await loop.run_in_executor(
                None, explain_ai.explain_drug, request.question
            )
            
        elif classification == "warn":
            # 약물 경고 AI 호출
            print("[INFO] WarnAI 호출 중...")
            _, warn_ai = get_specialized_agents()
            agent_used = "WarnAI"
            ai_response = await loop.run_in_executor(
                None, warn_ai.get_drug_warnings, request.question
            )
            
        elif classification == "add_cal":
            # 캘린더 AI 호출
            print("[INFO] CalendarAI 호출 중...")
            explain_ai, warn_ai, calendar_ai = get_specialized_agents()
            agent_used = "CalendarAI"
            
            # 사용자 세션 확인 (약물 정보 대기 중인지)
            user_id = "default"  # 실제로는 사용자 ID 사용
            
            if user_id in _user_sessions and _user_sessions[user_id].get('waiting_confirmation'):
                # 2단계: 사용자 확인 응답 처리
                if calendar_ai.check_confirmation(request.question):
                    # 캘린더 추가 진행
                    original_text = _user_sessions[user_id]['medication_text']
                    result = calendar_ai.process_calendar_addition(original_text)
                    
                    if result['success']:
                        ai_response = f"✅ 성공적으로 캘린더에 추가되었습니다!\n\n{result['message']}"
                    else:
                        ai_response = f"❌ 캘린더 추가 실패\n\n{result['message']}"
                    
                    # 세션 정리
                    del _user_sessions[user_id]
                else:
                    # 거부 응답
                    ai_response = "알겠습니다. 캘린더 추가를 취소했습니다. 다른 도움이 필요하시면 언제든 말씀해주세요."
                    del _user_sessions[user_id]
            else:
                # 1단계: 약물 정보 분석 + 제안
                ai_response = await loop.run_in_executor(
                    None, calendar_ai.analyze_medication_schedule, request.question
                )
                
                # 캘린더 추가 제안이 포함되어 있으면 세션 저장
                if "캘린더에 추가" in ai_response:
                    _user_sessions[user_id] = {
                        'waiting_confirmation': True,
                        'medication_text': request.question
                    }



            
        else:
            # 일반 대화 - 메인 채팅에서 직접 처리
            print("[INFO] 일반 대화 처리 중...")
            agent_used = "MainChat"
            
            general_prompt = f"""당신은 전문적인 의료 AI 어시스턴트입니다. 다음 지침을 따라 응답해주세요:

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
            
            ai_response = await loop.run_in_executor(
                None, get_medical_completion, general_prompt
            )
        
        # 성공 응답 반환
        return {
            "answer": ai_response.strip(),
            "user_context": {
                "underlying_diseases": request.underlying_diseases,
                "medications": request.currentMedications
            },
            "model_metadata": {
                "classification": classification,
                "agent_used": agent_used,
                "model_name": "IBM Granite 3.3 8B Instruct",
                "model_provider": "IBM Watson",
                "context_provided": bool(user_context),
                "disclaimer": "이는 일반적인 건강 정보이며, 전문 의료진의 진료를 대체할 수 없습니다."
            },
            "status": "success"
        }
        
    except Exception as e:
        # 실패 시 fallback 응답
        print(f"[ERROR] 채팅 처리 실패: {str(e)}")
        return await _get_fallback_response(request, f"처리 실패: {str(e)}")

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
- 규칙적인 생활습간과 충분한 휴식을 취하세요

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
        test_model = get_watson_model()
        if test_model:
            watson_status = "healthy"
        else:
            watson_status = "unavailable"
            watson_error = "Model instance creation failed"
    except Exception as e:
        watson_status = "error"
        watson_error = str(e)

    # 전문 AI 에이전트들 상태 확인
    agents_status = {}
    try:
        explain_ai, warn_ai, calendar_ai = get_specialized_agents()  # calendar_ai 받기
        agents_status = {
            "ExplainAI": "healthy" if explain_ai else "unavailable",
            "WarnAI": "healthy" if warn_ai else "unavailable",
            "CalendarAI": "healthy" if calendar_ai else "unavailable"  # pending -> healthy로 변경
        }
    except Exception as e:
        agents_status = {
            "error": f"전문 AI 에이전트 초기화 실패: {str(e)}"
        }


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
        "specialized_agents_status": agents_status,
        "all_configured": all_configured,
        "model_id": "ibm/granite-3-3-8b-instruct",
        "architecture": "Main Chat + Specialized Agents",
        "message": "메인 채팅과 전문 AI들이 정상 작동 중입니다." if overall_status == "healthy" else "시스템 설정을 확인하세요."
    }
