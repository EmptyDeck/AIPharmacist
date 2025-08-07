import httpx
import requests
import json
from fastapi import APIRouter, HTTPException
from schemas.chat import ChatRequest
from core.config import settings
import asyncio
from typing import Optional
from .chatbot.explainAI import ExplainAI
from .chatbot.warnAI import WarnAI
from .chatbot.calendarAI import CalendarAI

# APIRouter 인스턴스 생성
router = APIRouter()

# 전문 AI 에이전트 인스턴스들
_explain_ai: Optional[ExplainAI] = None
_warn_ai: Optional[WarnAI] = None
_calendar_ai: Optional[CalendarAI] = None

# 사용자 세션 저장 (실제로는 Redis나 DB 사용)
_user_sessions = {}

# IBM Watson 토큰 캐시
_watson_token_cache = {"token": None, "expires_at": 0}

def get_watson_token() -> str:
    """IBM Watson API 토큰을 발급받습니다"""
    import time
    
    current_time = time.time()
    if (_watson_token_cache["token"] and 
        current_time < _watson_token_cache["expires_at"] - 300):
        return _watson_token_cache["token"]
    
    if not settings.WATSONX_API_KEY:
        raise HTTPException(status_code=500, detail="IBM Watson API 키가 설정되지 않았습니다.")
    
    try:
        token_response = requests.post(
            'https://iam.cloud.ibm.com/identity/token',
            data={
                "apikey": settings.WATSONX_API_KEY,
                "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'
            }
        )
        
        if token_response.status_code != 200:
            raise Exception(f"토큰 발급 실패: {token_response.status_code}")
            
        token_data = token_response.json()
        mltoken = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
        
        if not mltoken:
            raise Exception("토큰 발급 실패!")
        
        _watson_token_cache["token"] = mltoken
        _watson_token_cache["expires_at"] = current_time + expires_in
        
        return mltoken
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IBM Watson 토큰 발급 실패: {str(e)}")

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

def call_llm(user_input: str) -> str:
    """LLM 호출해서 결과 받기"""
    try:
        mltoken = get_watson_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {mltoken}',
            'Accept': 'application/json'
        }
        
        ibm_ai_service_url = getattr(settings, 'WATSONX_DEPLOYMENT_URL', 
                                   'https://us-south.ml.cloud.ibm.com/ml/v1/deployments/b53e3a10-1ac5-4018-a0c2-29dda45e57f2/text/generation?version=2021-05-01')
        
        payload_scoring = {
            "parameters": {
                "prompt_variables": {
                    "default": user_input
                }
            }
        }
        
        response = requests.post(
            ibm_ai_service_url,
            headers=headers,
            json=payload_scoring,
            stream=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'results' in result and len(result['results']) > 0:
                generated_text = result['results'][0]['generated_text']
                first_line = generated_text.split('\n\nInput')[0].strip()
                return first_line
            else:
                return "응답에서 결과를 찾을 수 없습니다."
        else:
            raise Exception(f"API 호출 실패: {response.status_code}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {str(e)}")

@router.post("/chat", summary="의료 AI 채팅")
async def get_chat_response(request: ChatRequest):
    """메인 채팅 엔드포인트 - 캘린더 2단계 처리 포함"""
    
    try:
        loop = asyncio.get_event_loop()
        user_id = "default"  # 실제로는 사용자 ID 사용
        
        # 캘린더 확인 응답 대기 중인지 체크
        if user_id in _user_sessions and _user_sessions[user_id].get('waiting_calendar_confirmation'):
            print(f"[INFO] 캘린더 확인 응답 처리 중: {request.question}")
            
            _, _, calendar_ai = get_specialized_agents()
            
            # 사용자가 긍정적으로 답했는지 확인
            if calendar_ai.check_confirmation(request.question):
                # 캘린더에 추가 진행
                original_text = _user_sessions[user_id]['original_medication_text']
                result = await loop.run_in_executor(
                None, calendar_ai.process_calendar_addition, user_id, original_text
                )

                
                if result['success']:
                    ai_response = f"✅ 성공적으로 캘린더에 추가되었습니다!\n\n{result['message']}"
                else:
                    ai_response = f"❌ 캘린더 추가 실패\n\n{result['message']}"
                
                agent_used = "CalendarAI-Step2"
            else:
                # 거부 응답
                ai_response = "알겠습니다. 캘린더 추가를 취소했습니다. 다른 도움이 필요하시면 언제든 말씀해주세요."
                agent_used = "CalendarAI-Cancelled"
            
            # 세션 정리
            del _user_sessions[user_id]
            
            return {
                "answer": ai_response.strip(),
                "user_context": {
                    "underlying_diseases": request.underlying_diseases or [],
                    "medications": request.currentMedications or []
                },
                "model_metadata": {
                    "llm_classification": "calendar_confirmation",
                    "agent_used": agent_used,
                    "model_name": "IBM Watson (Calendar Processing)",
                    "status": "success"
                },
                "status": "success"
            }
        
        # 일반적인 LLM 분류 처리
        llm_response = await loop.run_in_executor(None, call_llm, request.question)
        print(f"[INFO] LLM 응답: {llm_response}")
        
        if llm_response == "warn":
            # WarnAI 호출
            _, warn_ai, _ = get_specialized_agents()
            ai_response = await loop.run_in_executor(None, warn_ai.get_drug_warnings, request.question)
            agent_used = "WarnAI"
            
        elif llm_response == "explain":
            # ExplainAI 호출
            explain_ai, _, _ = get_specialized_agents()
            ai_response = await loop.run_in_executor(None, explain_ai.explain_drug, request.question)
            agent_used = "ExplainAI"
            
        elif llm_response == "add_cal":
            # CalendarAI 1단계: 분석하고 확인 요청
            _, _, calendar_ai = get_specialized_agents()
            ai_response = await loop.run_in_executor(
                None, calendar_ai.analyze_medication_schedule, request.question
            )
            agent_used = "CalendarAI-Step1"
            
            # 세션에 저장해서 다음 응답 기다리기
            _user_sessions[user_id] = {
                'waiting_calendar_confirmation': True,
                'original_medication_text': request.question
            }
            print(f"[INFO] 캘린더 확인 대기 세션 생성: {user_id}")
            
        else:
            # 일반 대화 - LLM 응답 그대로 사용
            ai_response = llm_response
            agent_used = "MainChat"
        
        return {
            "answer": ai_response.strip(),
            "user_context": {
                "underlying_diseases": request.underlying_diseases or [],
                "medications": request.currentMedications or []
            },
            "model_metadata": {
                "llm_classification": llm_response,
                "agent_used": agent_used,
                "model_name": "IBM Watson (Simple Direct API)",
                "status": "success"
            },
            "status": "success"
        }
        
    except Exception as e:
        print(f"[ERROR] 채팅 처리 실패: {str(e)}")
        return await _get_fallback_response(request, str(e))

async def _get_fallback_response(request: ChatRequest, error_msg: str):
    """에러 발생시 fallback 응답"""
    user_context = []
    if request.underlying_diseases:
        user_context.append(f"기저질환: {', '.join(request.underlying_diseases)}")
    if request.currentMedications:
        user_context.append(f"복용약물: {', '.join(request.currentMedications)}")

    context_text = " | ".join(user_context) if user_context else "없음"

    fallback_response = f"""죄송합니다. 현재 AI 상담 서비스에 일시적인 문제가 발생했습니다.
오류: {error_msg}

귀하의 질문: "{request.question}"
사용자 정보: {context_text}."""

    return {
        "answer": fallback_response,
        "user_context": {
            "underlying_diseases": request.underlying_diseases or [],
            "medications": request.currentMedications or []
        },
        "status": "fallback",
        "error": error_msg
    }

@router.get("/health", summary="채팅 서비스 상태 확인")
async def health_check():
    """IBM Watson 연결 상태를 확인합니다."""

    config_status = {
        "WATSONX_API_KEY": bool(settings.WATSONX_API_KEY),
        "WATSONX_DEPLOYMENT_URL": bool(getattr(settings, 'WATSONX_DEPLOYMENT_URL', True))
    }

    watson_status = "unknown"
    watson_error = None

    try:
        token = get_watson_token()
        if token:
            watson_status = "healthy"
        else:
            watson_status = "unavailable"
            watson_error = "Token generation failed"
    except Exception as e:
        watson_status = "error"
        watson_error = str(e)

    agents_status = {}
    try:
        explain_ai, warn_ai, calendar_ai = get_specialized_agents()
        agents_status = {
            "ExplainAI": "healthy" if explain_ai else "unavailable",
            "WarnAI": "healthy" if warn_ai else "unavailable",
            "CalendarAI": "healthy" if calendar_ai else "unavailable"
        }
    except Exception as e:
        agents_status = {
            "error": f"전문 AI 에이전트 초기화 실패: {str(e)}"
        }

    all_configured = bool(settings.WATSONX_API_KEY)
    overall_status = "healthy" if watson_status == "healthy" and all_configured else "degraded"

    return {
        "service": "Dr.Watson Chat API (Calendar 2-Step)",
        "status": overall_status,
        "config_status": config_status,
        "watson_api_status": watson_status,
        "watson_error": watson_error,
        "specialized_agents_status": agents_status,
        "active_sessions": len(_user_sessions),
        "all_configured": all_configured,
        "api_method": "Direct requests API with Calendar 2-step process",
        "architecture": "LLM Classification + Specialized Agents + Calendar Session",
        "message": "캘린더 2단계 처리가 포함된 간단한 시스템입니다." if overall_status == "healthy" else "시스템 설정을 확인하세요."
    }
