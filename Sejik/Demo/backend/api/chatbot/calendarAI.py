# api/chatbot/calendarAI.py
import os
import logging
from core.config import settings
from utils.googleCalender.text_to_cal_json import text_to_cal_converter
from utils.googleCalender.cal_agent import calendar_agent       # 싱글톤
import google.generativeai as genai


class CalendarAI:
    def __init__(self):
        # API-KEY → 환경변수
        os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
        self.client = genai.Client()              # 코드2와 동일
        self.model_id = "gemini-2.0-flash-001"      # 고정 사용

    # ----------------------------
    # LLM 호출 (코드2 방식 그대로)
    # ----------------------------
    def get_completion(self,
                       prompt: str,
                       max_tokens: int = 200,        # ← 인터페이스만 유지
                       temperature: float = 0.7) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logging.error(f"🛑 CalendarAI(Gemini) 호출 실패: {e}")
            raise Exception(f"CalendarAI(Gemini) 호출 실패: {e}")

    # ─────────────────────────────────────────────
    # 1단계 – 분석 & “추가해드릴까요?” 문장 생성
    # ─────────────────────────────────────────────

    def analyze_medication_schedule(self, user_question: str) -> str:
        """
        사용자 질문을 요약·정리하고 캘린더 추가를 제안하는 응답 생성
        """
        prompt = f"""당신은 약물 복용 일정 관리 전문 AI 챗봇입니다.
        사용자의 약물 관련 요청을 분석한 뒤, 복약 정보를 명확히 정리해주고
        "이 약물 복용 일정을 구글 캘린더에 추가해드릴까요?" 로 끝맺어 주세요.

        <응답 형식>
        1. 약물 정보 분석
        - 약물명과 용량
        - 복용 시간대(아침·점심·저녁 등)
        - 복용 기간(몇 일·몇 주)
        - 복용 방법(식전/식후 등)
        2. 복용 일정 제안
        - 구체적인 복용 시간
        - 총 복용 기간
        3. 캘린더 추가 여부 질문

        사용자 질문: 『{user_question}』
        """
        return self.get_completion(prompt)

    # ─────────────────────────────────────────────
    # 1.5단계 – 실제 캘린더에 추가
    # ─────────────────────────────────────────────
    def check_confirmation(self, user_response: str) -> bool:
        """
        사용자가 캘린더 추가에 동의(Yes)했는지 여부를 반환.
        ① 부정어가 하나라도 포함되면 → 즉시 False
        ② 부정어가 없고, 긍정어가 포함돼 있으면 → True
        ③ 둘 다 없으면 → False
        """
        resp = user_response.lower().replace(" ", "")   # 공백 제거해 어절 결합형도 잡음

        # 부정 단어/어구  ─ 항상 최우선
        negatives = [
            "추가하지마", "하지마", "안해", "취소", "취소해", "싫어", "아니", "no", "n",
            "cancel", "stop", "그만", "dont", "do not", "안돼", "안되", "괜찮아"
        ]
        if any(n in resp for n in negatives):
            return False

        # 긍정 단어/어구
        positives = [
            "응", "어", "그래", "추가", "네", "yes", "y",
            "좋아", "해줘", "부탁", "ㅇㅇ", "please", "add", "ok", "확인"
        ]
        return any(p in resp for p in positives)

    # ───────────────────────────────
    # 2단계 – 실제 캘린더에 추가
    # ───────────────────────────────

    def process_calendar_addition(self, *args) -> dict:
        """
        호출 형태 2가지를 모두 지원한다.
        ① calendar_ai.process_calendar_addition(original_text)          # 새 버전
        ② calendar_ai.process_calendar_addition(user_id, original_text) # 옛 코드

        user_id 는 무시하고, 단일 계정용 calendar_agent 안에서 token.json 로 처리한다.
        """
        # ---------------- 인자 파싱 -----------------
        if len(args) == 1:
            original_text = args[0]
        elif len(args) == 2:
            # 첫 번째는 user_id 였던 값 → 호환만 위해 받고 버린다
            original_text = args[1]
        else:
            raise TypeError(
                "process_calendar_addition() takes (original_text) "
                "or (user_id, original_text)"
            )

        # 1) 자연어 → 이벤트 배열
        events = text_to_cal_converter.process_medication_text(original_text)
        if not events:
            return {
                "success": False,
                "message": "복약 정보를 캘린더 형식으로 변환할 수 없습니다."
            }

        # 2) Google Calendar 에 실제 추가
        result = calendar_agent.add_medication_schedule(events)
        return result | {"added_count": result.get("events_added", 0)}


# ─────────────────────────────────────────────
# 모듈 import 시 바로 쓸 수 있는 싱글톤
# ─────────────────────────────────────────────
calendar_ai = CalendarAI()


# ────────────────  간단 CLI 테스트  ────────────────
if __name__ == "__main__":
    qs = [
        "타이레놀 500mg을 하루 3번 아침점심저녁으로 3일간 먹어야 해",
        "오메프라졸 20mg 아침 식전에 2주간 복용",
        "아스피린 100mg 매일 저녁 식후에 먹으라고 했는데"
    ]
    for q in qs:
        print("Q :", q)
        print("A :", calendar_ai.analyze_medication_schedule(q))
        print("-" * 80)
