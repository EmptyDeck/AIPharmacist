from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GoogleAuthRequest(BaseModel):
    user_id: str


class GoogleTokenInfo(BaseModel):
    user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list


class CalendarRequestWithUser(BaseModel):
    user_id: str
    medication_text: str
    start_date: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    name: str
    google_id: Optional[str] = None
    profile_picture: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserWithToken(User):
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None