from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
from core.config import settings
import os




# APIRouter 인스턴스 생성
router = APIRouter()

# 이메일 설정 (네이버 SMTP)
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "test@naver.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "test_password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "test@naver.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.naver.com",  # 네이버 SMTP 서버
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# 이메일 요청 모델
class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str
    html_body: str = None

class BulkEmailRequest(BaseModel):
    recipients: List[EmailStr]
    subject: str
    body: str
    html_body: str = None


@router.post("/send", summary="단일 이메일 전송")
async def send_email(email_request: EmailRequest, background_tasks: BackgroundTasks):
    """1명에게 이메일을 전송합니다."""
    
    if not all([conf.MAIL_USERNAME, conf.MAIL_PASSWORD, conf.MAIL_FROM]):
        raise HTTPException(
            status_code=500, 
            detail="이메일 설정이 올바르지 않습니다"
        )
    
    message = MessageSchema(
        subject=email_request.subject,
        recipients=[email_request.recipient],
        body=email_request.html_body or email_request.body,
        subtype="html" if email_request.html_body else "plain"
    )
    
    fm = FastMail(conf)
    
    try:
        background_tasks.add_task(fm.send_message, message)
        return {"message": "이메일 전송 성공", "recipient": email_request.recipient}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 전송 실패: {str(e)}")


@router.post("/send-bulk", summary="다중 이메일 전송")
async def send_bulk_email(email_request: BulkEmailRequest, background_tasks: BackgroundTasks):
    """2명이상에게 이메일을 전송합니다. (최대 50명)"""
    
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
    
    message = MessageSchema(
        subject=email_request.subject,
        recipients=email_request.recipients,
        body=email_request.html_body or email_request.body,
        subtype="html" if email_request.html_body else "plain"
    )
    
    fm = FastMail(conf)
    
    try:
        background_tasks.add_task(fm.send_message, message)
        return {
            "message": "다중 이메일 전송 성공", 
            "recipient_count": len(email_request.recipients)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다중 이메일 전송 실패: {str(e)}")


@router.get("/test", summary="이메일 설정 테스트")
async def test_email_config():
    """이메일 설정이 올바른지 테스트합니다."""
    
    config_status = {
        "MAIL_USERNAME": bool(conf.MAIL_USERNAME),
        "MAIL_PASSWORD": bool(conf.MAIL_PASSWORD),
        "MAIL_FROM": bool(conf.MAIL_FROM),
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