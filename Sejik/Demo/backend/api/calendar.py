# # from fastapi import APIRouter, HTTPException
# # from pydantic import BaseModel
# # # from api.chatbot.calendarAI import calendar_ai
# # from utils.googleCalender import calendar_agent
# # from datetime import datetime
# # from typing import Optional, List
# import google.generativeai as genai

# # router = APIRouter()


# # class CalendarRequest(BaseModel):
# #     user_id: str
# #     medication_text: str
# #     start_date: Optional[str] = None  # ISO format: "2025-01-15T09:00:00"


# # class CalendarResponse(BaseModel):
# #     success: bool
# #     message: str
# #     events_added: int
# #     created_events: Optional[List[dict]] = None


# # @router.post("/add-medication", response_model=CalendarResponse, summary="복약 일정 추가")
# # async def add_medication_schedule(request: CalendarRequest):
# #     """복약 정보를 받아서 Google Calendar에 일정을 추가합니다."""

# #     try:
# #         start_date = None
# #         if request.start_date:
# #             try:
# #                 # 다양한 날짜 형식 처리
# #                 date_str = request.start_date.strip()

# #                 # ISO 형식 시도
# #                 if 'T' in date_str:
# #                     start_date = datetime.fromisoformat(
# #                         date_str.replace('Z', '+00:00'))
# #                 else:
# #                     # 간단한 날짜 형식들 처리
# #                     from dateutil import parser
# #                     start_date = parser.parse(date_str)

# #             except Exception as date_error:
# #                 print(f"날짜 파싱 실패: {date_error}, 기본값 사용")
# #                 start_date = None

# #         result = calendar_agent.process_medication_request(
# #             request.user_id,
# #             request.medication_text,
# #             start_date
# #         )

# #         return CalendarResponse(
# #             success=result['success'],
# #             message=result['message'],
# #             events_added=result['events_added'],
# #             created_events=result.get('created_events', [])
# #         )

# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"캘린더 일정 추가 실패: {str(e)}"
# #         )


# # @router.get("/upcoming", summary="다가오는 복약 일정 조회")
# # async def get_upcoming_schedules(user_id: str, days: int = 7):
# #     """앞으로 N일간의 복약 일정을 조회합니다."""

# #     try:
# #         events = calendar_agent.get_upcoming_medication_events(user_id, days)

# #         return {
# #             "success": True,
# #             "events_count": len(events),
# #             "events": events,
# #             "message": f"{days}일간 {len(events)}개의 복약 일정이 있습니다."
# #         }

# #     except Exception as e:
# #         raise HTTPException(
# #             status_code=500,
# #             detail=f"복약 일정 조회 실패: {str(e)}"
# #         )


# # @router.get("/health", summary="Google Calendar 연결 상태 확인")
# # async def calendar_health_check(user_id: str):
# #     """Google Calendar API 연결 상태를 확인합니다."""

# #     try:
# #         # 사용자 인증 상태 확인
# #         is_authenticated = calendar_agent.is_user_authenticated(user_id)

# #         if is_authenticated:
# #             # 간단한 API 호출 테스트
# #             events = calendar_agent.get_upcoming_medication_events(user_id, 1)

# #             return {
# #                 "service": "Google Calendar API",
# #                 "user_id": user_id,
# #                 "status": "healthy",
# #                 "authenticated": True,
# #                 "test_query_success": True,
# #                 "message": f"사용자 {user_id}의 Google Calendar 연결이 정상입니다."
# #             }
# #         else:
# #             return {
# #                 "service": "Google Calendar API",
# #                 "user_id": user_id,
# #                 "status": "error",
# #                 "authenticated": False,
# #                 "message": f"사용자 {user_id}의 Google Calendar 인증이 필요합니다."
# #             }

# #     except Exception as e:
# #         return {
# #             "service": "Google Calendar API",
# #             "status": "error",
# #             "authenticated": False,
# #             "error": str(e),
# #             "message": "Google Calendar 연결 중 오류가 발생했습니다."
# #         }
