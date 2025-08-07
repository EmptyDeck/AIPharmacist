# backend/utils/googleCalender/text_to_cal_json.py
import json, re, requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pytz
from core.config import settings


class TextToCalendarJSON:
    """
    자연어 복약 지시사항 → Google Calendar 이벤트 변환
    Watson-X Deployment(프롬프트 내장) 호출 → JSON 파싱 → 이벤트 생성
    """

    # ────────────────────────────────────
    # 0. 초기화
    # ────────────────────────────────────
    def __init__(self):
        self.endpoint = getattr(
            settings,
            "WATSONX_DEPLOYMENT_URL",
            "https://us-south.ml.cloud.ibm.com/ml/v1/deployments/18d4a2e6-add0-4215-a0cb-c67ab4130f90/text/generation?version=2021-05-01"
        )
        self.api_key   = settings.WATSONX_API_KEY
        self.korea_tz  = pytz.timezone("Asia/Seoul")
        self._token: Optional[str] = None        # IAM 토큰 캐시

    # ────────────────────────────────────
    # 1. IAM 토큰
    # ────────────────────────────────────
    def _get_token(self) -> str:
        if self._token:
            return self._token

        res = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "apikey": self.api_key,
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            },
            timeout=30,
        )
        res.raise_for_status()
        self._token = res.json()["access_token"]
        return self._token

    # ────────────────────────────────────
    # 2. Watson X 호출 & JSON 추출
    # ────────────────────────────────────
    @staticmethod
    def _parse_json_response(text: str) -> dict:
        """
        ① '일정끝' 이전 텍스트만 사용  
        ② 첫 번째 중첩 JSON 블록을 꺼냄
        """
        if "일정끝" in text:
            text = text.split("일정끝")[0]

        # 첫 { 위치
        start = text.find("{")
        if start == -1:
            raise ValueError("JSON 시작 '{' 를 찾지 못했습니다.")

        bracket = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "{":
                bracket += 1
            elif text[i] == "}":
                bracket -= 1
                if bracket == 0:
                    end = i + 1
                    break
        if bracket != 0:
            raise ValueError("JSON 브래킷이 닫히지 않았습니다.")

        json_str = text[start:end]
        return json.loads(json_str)

    def extract_medication_json(self, user_text: str) -> dict:
        """
        Deployment 호출 → generated_text → JSON 딕셔너리 반환
        """
        payload = {
            "parameters": {
                "prompt_variables": {"default": user_text}
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
        }

        resp = requests.post(self.endpoint, json=payload,
                             headers=headers, timeout=60)
        resp.raise_for_status()
        gen_txt = resp.json().get("results", [{}])[0].get("generated_text", "")
        if not gen_txt:
            raise Exception("AI 응답이 비어 있습니다.")

        print(f"🤖 AI 응답 앞부분:\n{gen_txt[:250]}...\n")
        return self._parse_json_response(gen_txt)

    # ────────────────────────────────────
    # 3-A. Watson-X 포맷 → Google 이벤트
    # ────────────────────────────────────
    def _convert_watsonx_to_google_format(self, parsed: dict) -> List[dict]:
        """
        parsed 안에 'calendar_events' 가 있으면 날짜만 오늘 기준으로 조정해 그대로 사용.
        없으면 medications + schedule_info 로부터 이벤트를 생성.
        """
        events: List[dict] = []

        # ① 이미 만들어진 이벤트가 있는 경우
        if parsed.get("calendar_events"):
            today = datetime.now().date()
            for ev in parsed["calendar_events"]:
                ev = ev.copy()
                try:
                    # dateTime 의 날짜부분을 오늘(today) 로 교체
                    for key in ("start", "end"):
                        if "dateTime" in ev[key]:
                            _, tpart = ev[key]["dateTime"].split("T")
                            ev[key]["dateTime"] = f"{today}T{tpart}"
                except Exception:
                    pass
                events.append(ev)
            return events

        # ② medications → 직접 이벤트 생성
        meds = parsed.get("medications", [])
        sched = parsed.get("schedule_info", {})
        duration = sched.get("duration_days", 7)

        for med in meds:
            name = med.get("name", "약물")
            times = med.get("times", ["09:00"])
            for t in times:
                try:
                    h, m = map(int, t.split(":"))
                    start_dt = datetime.now(self.korea_tz).replace(
                        hour=h, minute=m, second=0, microsecond=0)
                    end_dt = start_dt + timedelta(minutes=30)
                    event = {
                        "summary": f"💊 {name} 복용",
                        "description": f"약물: {name}\n복용 시간: {t}\n⚠️ 정확한 시간에 복용하세요!",
                        "start": {
                            "dateTime": start_dt.isoformat(),
                            "timeZone": "Asia/Seoul",
                        },
                        "end": {
                            "dateTime": end_dt.isoformat(),
                            "timeZone": "Asia/Seoul",
                        },
                        "recurrence": [
                            f"RRULE:FREQ=DAILY;COUNT={duration}"
                        ],
                        "reminders": {
                            "useDefault": False,
                            "overrides": [
                                {"method": "popup", "minutes": 10},
                                {"method": "popup", "minutes": 0},
                            ],
                        },
                    }
                    events.append(event)
                except Exception as e:
                    print(f"시간 파싱 오류({t}): {e}")
        return events

    # ────────────────────────────────────
    # 3-B. (예전 간단 포맷) → Google 이벤트
    # ────────────────────────────────────
    def _convert_old_format(self, info: Dict,
                            start_date: Optional[datetime] = None) -> List[Dict]:
        """
        오래된 medication_name / times … 구조 지원
        (기존 코드1의 convert_to_calendar_events 내용 간소화 버전)
        """
        if not start_date:
            start_date = datetime.now(self.korea_tz).replace(
                hour=9, minute=0, second=0, microsecond=0)

        time_map = {"아침": 8, "점심": 12, "저녁": 18, "취침전": 21,
                    "식전": 7, "식후": 13}

        name = info.get("medication_name", "복용약")
        dosage = info.get("dosage", "1정")
        times = info.get("times", ["아침"])
        duration = info.get("duration_days", 7)
        special = info.get("special_instructions", "")

        events = []
        for t in times:
            hour = time_map.get(t, 9)
            st = start_date.replace(hour=hour, minute=0)
            et = st + timedelta(minutes=30)
            until = start_date + timedelta(days=duration)
            events.append(
                {
                    "summary": f"💊 {name} 복용 ({t})",
                    "description": f"복용약: {name}\n용량: {dosage}\n복용시간: {t}\n특별지시사항: {special}",
                    "start": {"dateTime": st.isoformat(), "timeZone": "Asia/Seoul"},
                    "end":   {"dateTime": et.isoformat(), "timeZone": "Asia/Seoul"},
                    "recurrence": [
                        f"RRULE:FREQ=DAILY;UNTIL={until.strftime('%Y%m%dT%H%M%SZ')}"
                    ],
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "popup", "minutes": 15},
                            {"method": "popup", "minutes": 5},
                        ],
                    },
                    "colorId": "10",
                }
            )
        return events

    # ────────────────────────────────────
    # 4. public 파이프라인
    # ────────────────────────────────────
    def process_medication_text(self,
                                user_text: str,
                                start_date: Optional[datetime] = None) -> List[Dict]:
        """
        1) Watson-X 호출 → JSON  
        2) calendar_events 가 있으면 그대로 / 없으면 옛 포맷으로 해석  
        3) Google Calendar 이벤트 리스트 반환
        """
        try:
            data = self.extract_medication_json(user_text)

            if "calendar_events" in data or "medications" in data:
                events = self._convert_watsonx_to_google_format(data)
            else:
                events = self._convert_old_format(data, start_date)

            print(f"✅ 이벤트 {len(events)}개 생성")
            return events

        except Exception as e:
            # 실패 시 1회성 기본 알림
            print(f"복약 정보 처리 실패: {e}")
            dt = datetime.now(self.korea_tz) if not start_date else start_date
            return [{
                "summary": "💊 복용약 알림",
                "description": f"처방: {user_text}\n\n의사·약사 지시에 따라 복용하세요.",
                "start": {"dateTime": dt.isoformat(), "timeZone": "Asia/Seoul"},
                "end":   {"dateTime": (dt + timedelta(minutes=30)).isoformat(),
                          "timeZone": "Asia/Seoul"},
                "recurrence": ["RRULE:FREQ=DAILY;COUNT=7"],
                "reminders": {"useDefault": False,
                              "overrides": [{"method": "popup", "minutes": 15}]},
                "colorId": "10",
            }]


# 싱글톤 인스턴스
text_to_cal_converter = TextToCalendarJSON()
