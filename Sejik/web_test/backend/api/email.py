from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
from core.config import settings
import os




# APIRouter 인스턴스 생성
router = APIRouter()

# 이메일 설정 (Gmail SMTP)
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",  # Gmail SMTP 서버
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False  # SSL 검증 비활성화로 시도
)

# 이메일 요청 모델
class ChatEmailRequest(BaseModel):
    recipient: EmailStr
    patient_name: str
    chat_history: str  # 모델과의 대화 내용
    doctor_name: str = "IBM_DoctorAI"

class BulkChatEmailRequest(BaseModel):
    recipients: List[EmailStr]
    patient_name: str
    chat_history: str  # 모델과의 대화 내용
    doctor_name: str = "IBM_DoctorAI"


@router.post("/send", summary="AI 상담 결과 이메일 단일 전송")
async def send_chat_email(email_request: ChatEmailRequest, background_tasks: BackgroundTasks):
    """AI 상담 결과를 이메일로 전송합니다."""
    
    if not all([conf.MAIL_USERNAME, conf.MAIL_PASSWORD, conf.MAIL_FROM]):
        raise HTTPException(
            status_code=500, 
            detail="이메일 설정이 올바르지 않습니다"
        )
    
    # 제목 템플릿 (고정)
    subject = f"{email_request.patient_name}님의 IBM_DoctorAI 의료상담결과"
    
    # 본문 템플릿 + 채팅 내용
    from datetime import datetime
    current_date = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    body = f"""안녕하세요.

{email_request.patient_name}님의 IBM_DoctorAI 의료상담결과를 전송해드립니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 AI 상담 내용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{email_request.chat_history}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  중요 안내:
• 본 상담 결과는 AI 기반 분석이며, 의학적 진단이 아닙니다.
• 정확한 진단은 반드시 의료진과 상담하시기 바랍니다.
• 응급상황 시 즉시 119 또는 가까운 응급실로 연락하세요.

상담일시: {current_date}
담당 AI: {email_request.doctor_name}

감사합니다.
IBM_DoctorAI 팀 드림
"""
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_request.recipient],
        body=body,
        subtype="plain"
    )
    
    fm = FastMail(conf)
    
    try:
        await fm.send_message(message)
        return {
            "message": "AI 상담 결과 이메일 전송 성공",
            "recipient": email_request.recipient,
            "patient_name": email_request.patient_name,
            "subject": subject
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 전송 실패: {str(e)}")


@router.post("/send-bulk", summary="AI 상담 결과 이메일 다중 전송")
async def send_bulk_chat_email(email_request: BulkChatEmailRequest, background_tasks: BackgroundTasks):
    """AI 상담 결과를 여러 명에게 이메일로 전송합니다. (최대 50명)"""
    
    # 수신자 수 제한 확인
    if len(email_request.recipients) > 50:
        raise HTTPException(
            status_code=400,
            detail=f"최대 50명까지 이메일 전송 가능합니다. 현재: {len(email_request.recipients)}명"
        )
    
    if len(email_request.recipients) < 2:
        raise HTTPException(
            status_code=400,
            detail="다중 이메일 전송은 최소 2명 이상이어야 합니다."
        )
    
    if not all([conf.MAIL_USERNAME, conf.MAIL_PASSWORD, conf.MAIL_FROM]):
        raise HTTPException(
            status_code=500, 
            detail="이메일 설정이 올바르지 않습니다"
        )
    
    # 제목 템플릿 (고정)
    subject = f"{email_request.patient_name}님의 IBM_DoctorAI 의료상담결과"
    
    # 본문 템플릿 + 채팅 내용
    from datetime import datetime
    current_date = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    body = f"""안녕하세요.

{email_request.patient_name}님의 IBM_DoctorAI 의료상담결과를 전송해드립니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 AI 상담 내용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{email_request.chat_history}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  중요 안내:
• 본 상담 결과는 AI 기반 분석이며, 의학적 진단이 아닙니다.
• 정확한 진단은 반드시 의료진과 상담하시기 바랍니다.
• 응급상황 시 즉시 119 또는 가까운 응급실로 연락하세요.

상담일시: {current_date}
담당 AI: {email_request.doctor_name}

감사합니다.
IBM_DoctorAI 팀 드림
"""
    
    message = MessageSchema(
        subject=subject,
        recipients=email_request.recipients,
        body=body,
        subtype="plain"
    )
    
    fm = FastMail(conf)
    
    try:
        await fm.send_message(message)
        return {
            "message": "AI 상담 결과 다중 이메일 전송 성공", 
            "recipient_count": len(email_request.recipients),
            "patient_name": email_request.patient_name,
            "subject": subject
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다중 이메일 전송 실패: {str(e)}")


@router.get("/test", summary="이메일 설정 테스트")
async def test_email_config():
    """이메일 설정이 올바른지 테스트합니다."""
    
    config_status = {
        "MAIL_USERNAME": conf.MAIL_USERNAME,
        "MAIL_PASSWORD": f"***{str(conf.MAIL_PASSWORD)[-4:]}" if conf.MAIL_PASSWORD else None,
        "MAIL_FROM": conf.MAIL_FROM,
        "MAIL_SERVER": conf.MAIL_SERVER,
        "MAIL_PORT": conf.MAIL_PORT
    }
    
    all_configured = all([
        conf.MAIL_USERNAME, 
        conf.MAIL_PASSWORD, 
        conf.MAIL_FROM
    ])
    
    return {
        "configured": all_configured,
        "config_status": config_status,
        "message": "이메일 서비스 준비 완료" if all_configured else "이메일 서비스 설정이 필요합니다"
    }