from pydantic import BaseModel
from typing import Optional


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