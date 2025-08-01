from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
from core.config import settings
import os




# APIRouter instance creation
router = APIRouter()

# Email configuration (Naver SMTP)
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

# Email request models
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


@router.post("/send", summary="Send single email")
async def send_email(email_request: EmailRequest, background_tasks: BackgroundTasks):
    """Send a single email."""
    
    if not all([conf.MAIL_USERNAME, conf.MAIL_PASSWORD, conf.MAIL_FROM]):
        raise HTTPException(
            status_code=500, 
            detail="Email configuration not properly set"
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
        return {"message": "Email sent successfully", "recipient": email_request.recipient}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/send-bulk", summary="Send bulk email")
async def send_bulk_email(email_request: BulkEmailRequest, background_tasks: BackgroundTasks):
    """Send the same email to multiple recipients."""
    
    if not all([conf.MAIL_USERNAME, conf.MAIL_PASSWORD, conf.MAIL_FROM]):
        raise HTTPException(
            status_code=500, 
            detail="Email configuration not properly set"
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
            "message": "Bulk email sent successfully", 
            "recipient_count": len(email_request.recipients)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send bulk email: {str(e)}")


@router.get("/test", summary="Test email configuration")
async def test_email_config():
    """Test if email configuration is correct."""
    
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
        "message": "Email service is ready" if all_configured else "Email service needs configuration"
    }