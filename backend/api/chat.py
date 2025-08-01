
import httpx
from fastapi import APIRouter, HTTPException
from schemas.chat import ChatRequest
from core.config import settings

# APIRouter 인스턴스 생성
router = APIRouter()


@router.post("/chat", summary="의료 AI 채팅")
async def get_chat_response(request: ChatRequest):
    """프론트엔드 요청을 팀원 AI 모델로 전송하고 응답을 반환합니다.(중계)"""
    
    # 팀원 모델로 전송할 데이터 구성
    model_request = {
        "question": request.question,
        "underlying_diseases": request.underlying_diseases or [],   # 기저질환
        "medications": request.currentMedications or []             # 복용중인 약물
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # API 키가 설정되어 있다면 헤더에 추가
    if settings.MODEL_API_KEY:
        headers["Authorization"] = f"Bearer {settings.MODEL_API_KEY}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 팀원 모델 API에 요청 전송
            response = await client.post(
                f"{settings.MODEL_API_URL}/predict",  # 팀원 모델의 예측 엔드포인트
                json=model_request,
                headers=headers
            )
            response.raise_for_status()
            
            # 팀원 모델의 응답을 프론트엔드에 전달
            model_response = response.json()
            
            return {
                "answer": model_response.get("answer", model_response.get("response", "")),
                "user_context": {
                    "underlying_diseases": request.underlying_diseases,
                    "medications": request.currentMedications
                },
                "model_metadata": model_response.get("metadata", {}),
                "status": "success"
            }
                
    except httpx.TimeoutException:
        # 타임아웃 시 기본 응답 제공
        return await _get_fallback_response(request, "AI 모델 서버 응답 시간 초과")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return await _get_fallback_response(request, "AI 모델 서버를 찾을 수 없음")
        else:
            return await _get_fallback_response(request, f"AI 모델 서버 오류: {e.response.status_code}")
    except httpx.ConnectError:
        # 연결 실패 시 기본 응답 제공
        return await _get_fallback_response(request, "AI 모델 서버에 연결할 수 없음")
    except Exception as e:
        return await _get_fallback_response(request, f"내부 서버 오류: {str(e)}")


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
    """채팅 서비스와 팀원 모델의 연결 상태를 확인합니다."""
    
    # 설정 상태 확인
    config_status = {
        "MODEL_API_URL": bool(settings.MODEL_API_URL),
        "MODEL_API_KEY": bool(settings.MODEL_API_KEY) if settings.MODEL_API_KEY else "not_required"
    }
    
    # 팀원 모델 서비스 연결 테스트
    model_service_status = "unknown"
    model_error = None
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 팀원 모델의 health 엔드포인트 확인
            test_response = await client.get(f"{settings.MODEL_API_URL}/health")
            if test_response.status_code == 200:
                model_service_status = "healthy"
            else:
                model_service_status = "unhealthy"
                model_error = f"HTTP {test_response.status_code}"
    except httpx.ConnectError:
        model_service_status = "unavailable"
        model_error = "Connection refused"
    except httpx.TimeoutException:
        model_service_status = "timeout"
        model_error = "Connection timeout"
    except Exception as e:
        model_service_status = "error"
        model_error = str(e)
    
    overall_status = "healthy" if model_service_status == "healthy" else "degraded"
    
    return {
        "service": "Chat API",
        "status": overall_status,
        "config_status": config_status,
        "model_service_status": model_service_status,
        "model_api_url": settings.MODEL_API_URL,
        "model_error": model_error,
        "message": "AI 모델 서버가 정상 작동 중입니다." if overall_status == "healthy" else "AI 모델 서버 연결에 문제가 있습니다. 기본 응답으로 동작합니다."
    }