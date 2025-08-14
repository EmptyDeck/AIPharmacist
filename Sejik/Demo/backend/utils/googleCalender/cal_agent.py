# import os
# from datetime import datetime, timedelta
# from typing import List, Dict, Optional

# import pytz
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

# from utils.googleCalender.text_to_cal_json import text_to_cal_converter

# os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"       # 개발용 http 허용


# class GoogleCalendarAgent:
#     """단일 Google 계정(credential.json)으로 복약 알림을 관리"""

#     SCOPES = ["https://www.googleapis.com/auth/calendar"]

#     def __init__(self):
#         self.korea_tz = pytz.timezone("Asia/Seoul")

#         base_dir = os.path.dirname(__file__)
#         self.client_secret_file = os.path.join(base_dir, "credentials.json")
#         self.token_file         = os.path.join(base_dir, "token.json")

#         self._service = None    # singleton service 객체

#     # ────────────────────────────────
#     # 1. Google Calendar 서비스 얻기
#     # ────────────────────────────────
#     def get_service(self):
#         if self._service:          # 이미 만들어졌으면 재사용
#             return self._service

#         creds: Optional[Credentials] = None

#         # token.json 이 있으면 로드
#         if os.path.exists(self.token_file):
#             creds = Credentials.from_authorized_user_file(
#                 self.token_file, self.SCOPES
#             )

#         # 없거나(refresh 필요) 유효하지 않으면 처리
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 if not os.path.exists(self.client_secret_file):
#                     raise FileNotFoundError("credentials.json 파일이 없습니다.")
#                 flow = InstalledAppFlow.from_client_secrets_file(
#                     self.client_secret_file, self.SCOPES
#                 )
#                 creds = flow.run_local_server(port=0)   # 브라우저 팝업

#             # 최신 토큰 저장
#             with open(self.token_file, "w") as f:
#                 f.write(creds.to_json())

#         # Calendar 서비스 생성
#         self._service = build("calendar", "v3", credentials=creds)
#         return self._service

#     # ────────────────────────────────
#     # 2. 중복 이벤트 체크
#     # ────────────────────────────────
#     def _check_existing_events(
#         self, medication_name: str, start: datetime, end: datetime
#     ) -> List[Dict]:
#         service = self.get_service()
#         try:
#             resp = (
#                 service.events()
#                 .list(
#                     calendarId="primary",
#                     timeMin=start.isoformat(),
#                     timeMax=end.isoformat(),
#                     q="💊",
#                     singleEvents=True,
#                     orderBy="startTime",
#                 )
#                 .execute()
#             )
#             return [
#                 evt
#                 for evt in resp.get("items", [])
#                 if evt.get("summary", "").startswith(f"💊 {medication_name}")
#             ]
#         except HttpError as e:
#             print(f"[ERROR] 중복 조회 실패: {e}")
#             return []

#     # ────────────────────────────────
#     # 3. 캘린더에 이벤트 추가
#     # ────────────────────────────────
#         # 3. 캘린더에 이벤트 추가  ─ 수정 버전
#     def add_medication_schedule(self, *args, **kwargs) -> Dict:
#         """
#         events 만 넘기거나, (user_id, events) 두 가지 호출 모두 지원한다.

#         예)
#             calendar_agent.add_medication_schedule(events)          # new
#             calendar_agent.add_medication_schedule(user_id, events) # legacy
#         """
#         # ------------------------------------
#         # 1) positional 인자 해석
#         # ------------------------------------
#         if len(args) == 1:
#             events = args[0]               # new 방식
#         elif len(args) == 2:
#             # 첫 번째 인자는 그냥 무시(호환용)
#             events = args[1]
#         else:
#             raise TypeError(
#                 "add_medication_schedule() takes [events] or [user_id, events]"
#             )

#         # ------------------------------------
#         # 2) 서비스 객체 확보
#         #    (단일 계정 모드이므로 self.get_service() 만 호출)
#         # ------------------------------------
#         service = self.get_service()
#         results = {
#             "success": True,
#             "events_added": 0,
#             "failed_events": [],
#             "created_events": [],
#         }

#         # ------------------------------------
#         # 3) 이벤트 반복 추가 (기존 로직 그대로)
#         # ------------------------------------
#         for evt in events:
#             try:
#                 med_name = evt["summary"].replace("💊 ", "").split(" 복용")[0]
#                 start_dt = datetime.fromisoformat(
#                     evt["start"]["dateTime"].replace("Z", "+00:00")
#                 )
#                 dup = self._check_existing_events(
#                     med_name, start_dt, start_dt + timedelta(days=30)
#                 )
#                 # if dup:
#                 #     print(f"[SKIP] 이미 존재 → {med_name}")
#                 #     continue

#                 created = (
#                     service.events().insert(calendarId="primary", body=evt).execute()
#                 )
#                 results["events_added"] += 1
#                 results["created_events"].append(
#                     {
#                         "id": created["id"],
#                         "summary": created["summary"],
#                         "start": created["start"].get("dateTime"),
#                         "html_link": created["htmlLink"],
#                     }
#                 )
#             except Exception as e:
#                 results["failed_events"].append(str(e))
#                 results["success"] = False

#         results["message"] = (
#             f"{results['events_added']}개 추가"
#             if results["events_added"]
#             else "추가된 이벤트가 없습니다."
#         )
#         return results


#     # ────────────────────────────────
#     # 4. 자연어 → 캘린더 파이프라인
#     # ────────────────────────────────
#     def process_medication_request(
#         self, medication_text: str, start_date: Optional[datetime] = None
#     ) -> Dict:
#         try:
#             events = text_to_cal_converter.process_medication_text(
#                 medication_text, start_date
#             )
#             if not events:
#                 return {"success": False, "message": "이벤트 변환 실패", "events_added": 0}

#             return self.add_medication_schedule(events) | {
#                 "processed_events": len(events),
#                 "medication_text": medication_text,
#             }
#         except Exception as e:
#             return {
#                 "success": False,
#                 "message": f"파이프라인 오류: {e}",
#                 "events_added": 0,
#                 "error": str(e),
#             }

#     # ────────────────────────────────
#     # 5. 다가오는 복약 일정 조회
#     # ────────────────────────────────
#     def get_upcoming_medication_events(self, days: int = 7) -> List[Dict]:
#         service = self.get_service()
#         now = datetime.now(self.korea_tz)
#         window = now + timedelta(days=days)

#         try:
#             items = (
#                 service.events()
#                 .list(
#                     calendarId="primary",
#                     timeMin=now.isoformat(),
#                     timeMax=window.isoformat(),
#                     q="💊",
#                     singleEvents=True,
#                     orderBy="startTime",
#                 )
#                 .execute()
#                 .get("items", [])
#             )
#             return [
#                 {
#                     "id": it["id"],
#                     "summary": it["summary"],
#                     "start": it["start"].get("dateTime"),
#                     "html_link": it.get("htmlLink"),
#                 }
#                 for it in items
#             ]
#         except HttpError as e:
#             print(f"[ERROR] 일정 조회 실패: {e}")
#             return []


# # 싱글톤 인스턴스
# calendar_agent = GoogleCalendarAgent()


# 내 개인 ibm 캘린더에 추가

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.googleCalender.text_to_cal_json import text_to_cal_converter

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"       # 개발용 http 허용


class GoogleCalendarAgent:
    """단일 Google 계정(credential.json)으로 복약 알림을 관리"""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self):
        self.korea_tz = pytz.timezone("Asia/Seoul")
        # 커스텀 캘린더 ID 설정
        self.calendar_id = "46e21dc8a28efb4888bf952ff88cd1514cf5dbea9faeb15615b75c1391cc2bc1@group.calendar.google.com"

        base_dir = os.path.dirname(__file__)
        self.client_secret_file = os.path.join(base_dir, "credentials.json")
        self.token_file = os.path.join(base_dir, "token.json")

        self._service = None    # singleton service 객체

    # ────────────────────────────────
    # 1. Google Calendar 서비스 얻기
    # ────────────────────────────────
    def get_service(self):
        if self._service:          # 이미 만들어졌으면 재사용
            return self._service

        creds: Optional[Credentials] = None

        # token.json 이 있으면 로드
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(
                self.token_file, self.SCOPES
            )

        # 없거나(refresh 필요) 유효하지 않으면 처리
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secret_file):
                    raise FileNotFoundError("credentials.json 파일이 없습니다.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)   # 브라우저 팝업

            # 최신 토큰 저장
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        # Calendar 서비스 생성
        self._service = build("calendar", "v3", credentials=creds)
        return self._service

    # ────────────────────────────────
    # 2. 중복 이벤트 체크
    # ────────────────────────────────
    def _check_existing_events(
        self, medication_name: str, start: datetime, end: datetime
    ) -> List[Dict]:
        service = self.get_service()
        try:
            resp = (
                service.events()
                .list(
                    calendarId=self.calendar_id,  # primary → 커스텀 캘린더 ID
                    timeMin=start.isoformat(),
                    timeMax=end.isoformat(),
                    q="💊",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return [
                evt
                for evt in resp.get("items", [])
                if evt.get("summary", "").startswith(f"💊 {medication_name}")
            ]
        except HttpError as e:
            print(f"[ERROR] 중복 조회 실패: {e}")
            return []

    # ────────────────────────────────
    # 3. 캘린더에 이벤트 추가
    # ────────────────────────────────
        # 3. 캘린더에 이벤트 추가  ─ 수정 버전
    def add_medication_schedule(self, *args, **kwargs) -> Dict:
        """
        events 만 넘기거나, (user_id, events) 두 가지 호출 모두 지원한다.

        예)
            calendar_agent.add_medication_schedule(events)          # new
            calendar_agent.add_medication_schedule(user_id, events) # legacy
        """
        # ------------------------------------
        # 1) positional 인자 해석
        # ------------------------------------
        if len(args) == 1:
            events = args[0]               # new 방식
        elif len(args) == 2:
            # 첫 번째 인자는 그냥 무시(호환용)
            events = args[1]
        else:
            raise TypeError(
                "add_medication_schedule() takes [events] or [user_id, events]"
            )

        # ------------------------------------
        # 2) 서비스 객체 확보
        #    (단일 계정 모드이므로 self.get_service() 만 호출)
        # ------------------------------------
        service = self.get_service()
        results = {
            "success": True,
            "events_added": 0,
            "failed_events": [],
            "created_events": [],
        }

        # ------------------------------------
        # 3) 이벤트 반복 추가 (기존 로직 그대로)
        # ------------------------------------
        for evt in events:
            try:
                med_name = evt["summary"].replace("💊 ", "").split(" 복용")[0]
                start_dt = datetime.fromisoformat(
                    evt["start"]["dateTime"].replace("Z", "+00:00")
                )
                dup = self._check_existing_events(
                    med_name, start_dt, start_dt + timedelta(days=30)
                )
                # if dup:
                #     print(f"[SKIP] 이미 존재 → {med_name}")
                #     continue

                created = (
                    service.events().insert(calendarId=self.calendar_id,
                                            # primary → 커스텀 캘린더 ID
                                            body=evt).execute()
                )
                results["events_added"] += 1
                results["created_events"].append(
                    {
                        "id": created["id"],
                        "summary": created["summary"],
                        "start": created["start"].get("dateTime"),
                        "html_link": created["htmlLink"],
                    }
                )
            except Exception as e:
                results["failed_events"].append(str(e))
                results["success"] = False

        results["message"] = (
            f"{results['events_added']}개 추가"
            if results["events_added"]
            else "추가된 이벤트가 없습니다."
        )
        return results

    # ────────────────────────────────
    # 4. 자연어 → 캘린더 파이프라인
    # ────────────────────────────────

    def process_medication_request(
        self, medication_text: str, start_date: Optional[datetime] = None
    ) -> Dict:
        try:
            events = text_to_cal_converter.process_medication_text(
                medication_text, start_date
            )
            if not events:
                return {"success": False, "message": "이벤트 변환 실패", "events_added": 0}

            return self.add_medication_schedule(events) | {
                "processed_events": len(events),
                "medication_text": medication_text,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"파이프라인 오류: {e}",
                "events_added": 0,
                "error": str(e),
            }

    # ────────────────────────────────
    # 5. 다가오는 복약 일정 조회
    # ────────────────────────────────
    def get_upcoming_medication_events(self, days: int = 7) -> List[Dict]:
        service = self.get_service()
        now = datetime.now(self.korea_tz)
        window = now + timedelta(days=days)

        try:
            items = (
                service.events()
                .list(
                    calendarId=self.calendar_id,  # primary → 커스텀 캘린더 ID
                    timeMin=now.isoformat(),
                    timeMax=window.isoformat(),
                    q="💊",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
                .get("items", [])
            )
            return [
                {
                    "id": it["id"],
                    "summary": it["summary"],
                    "start": it["start"].get("dateTime"),
                    "html_link": it.get("htmlLink"),
                }
                for it in items
            ]
        except HttpError as e:
            print(f"[ERROR] 일정 조회 실패: {e}")
            return []


# 싱글톤 인스턴스
calendar_agent = GoogleCalendarAgent()
