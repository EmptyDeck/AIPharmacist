from datetime import datetime
from typing import Dict, Optional
from utils.googleCalender import calendar_agent, text_to_cal_converter
import re


class CalendarAI:
    """복약 캘린더 관리를 위한 전문 AI 에이전트"""
    
    def __init__(self):
        self.user_sessions = {}  # 사용자별 세션 관리
    
    def analyze_medication_schedule(self, query: str, user_id: str = "default", user_context: dict = None) -> str:
        """복약 스케줄 분석 및 캘린더 추가 제안"""
        
        # 복약 관련 키워드 확인
        medication_keywords = [
            '복용', '먹어', '드세요', '정', '알', '캡슐', '시럽', '약', 
            '아침', '점심', '저녁', '식전', '식후', '취침', '하루', '일',
            '매일', '주간', '개월', '번', '회'
        ]
        
        has_medication_info = any(keyword in query for keyword in medication_keywords)
        
        if not has_medication_info:
            return """
죄송합니다. 복약 관련 정보를 찾을 수 없습니다. 

캘린더에 복약 일정을 추가하려면 다음과 같은 정보를 포함해서 말씀해 주세요:
- 약물명
- 복용 횟수 (하루 몇 번)
- 복용 시간 (아침, 점심, 저녁 등)
- 복용 기간

예시: "타이레놀 1정을 하루 3번 아침, 점심, 저녁 식후에 7일간 복용해야 해요"
"""
        
        # 세션에 복약 정보 저장
        self.user_sessions[user_id] = {
            'medication_text': query,
            'user_context': user_context,
            'status': 'pending_confirmation',
            'timestamp': datetime.now()
        }
        
        # 복약 정보 분석
        try:
            medication_info = text_to_cal_converter.extract_medication_info(query)
            
            # 분석 결과 표시
            analysis_text = f"""
📋 **복약 정보 분석 결과:**

💊 **약물명**: {medication_info.get('medication_name', '정보 없음')}
📏 **용량**: {medication_info.get('dosage', '정보 없음')}
🔄 **복용 횟수**: 하루 {medication_info.get('frequency', 1)}번
⏰ **복용 시간**: {', '.join(medication_info.get('times', ['아침']))}
📅 **복용 기간**: {medication_info.get('duration_days', 7)}일
📝 **특별 지시사항**: {medication_info.get('special_instructions', '없음')}

위 정보로 Google Calendar에 복약 알림을 추가하시겠습니까?

**"네, 추가해주세요"** 또는 **"추가"**라고 답하시면 캘린더에 일정을 등록해드립니다.
**"아니요"** 또는 **"취소"**라고 답하시면 취소됩니다.

⚠️ 정확한 복약을 위해 의사나 약사의 지시를 우선으로 따르세요.
"""
            
            return analysis_text
            
        except Exception as e:
            return f"복약 정보 분석 중 오류가 발생했습니다: {str(e)}\n다시 시도해 주세요."
    
    def check_confirmation(self, response: str, user_id: str = "default") -> str:
        """사용자 확인 응답 처리"""
        
        if user_id not in self.user_sessions:
            return "캘린더 추가할 복약 정보가 없습니다. 먼저 복약 정보를 말씀해 주세요."
        
        session = self.user_sessions[user_id]
        
        if session['status'] != 'pending_confirmation':
            return "현재 확인 대기 중인 요청이 없습니다."
        
        # 확인 키워드 체크
        positive_keywords = ['네', '예', '추가', '맞', '좋', '확인', 'yes', 'ok', '그래']
        negative_keywords = ['아니', '취소', '안', '싫', 'no', '됐']
        
        response_lower = response.lower().strip()
        
        is_positive = any(keyword in response_lower for keyword in positive_keywords)
        is_negative = any(keyword in response_lower for keyword in negative_keywords)
        
        if is_positive and not is_negative:
            # 캘린더 추가 실행
            return self.process_calendar_addition(user_id)
        elif is_negative:
            # 취소 처리
            del self.user_sessions[user_id]
            return "캘린더 추가를 취소했습니다. 언제든지 다시 요청해 주세요! 😊"
        else:
            return """
명확하지 않은 응답입니다. 다시 한 번 말씀해 주세요:

- 캘린더에 추가하시려면: **"네, 추가해주세요"**
- 취소하시려면: **"아니요, 취소합니다"**
"""
    
    def process_calendar_addition(self, user_id: str = "default") -> str:
        """실제 캘린더 추가 처리"""
        
        if user_id not in self.user_sessions:
            return "세션 정보를 찾을 수 없습니다."
        
        session = self.user_sessions[user_id]
        medication_text = session['medication_text']
        
        try:
            # 캘린더 에이전트를 통해 일정 추가
            result = calendar_agent.process_medication_request(medication_text)
            
            # 세션 정리
            del self.user_sessions[user_id]
            
            if result['success']:
                success_message = f"""
✅ **캘린더 추가 완료!**

📅 **{result['events_added']}개의 복약 알림**이 Google Calendar에 추가되었습니다.

{result['message']}

💡 **확인하기**: Google Calendar 앱이나 웹에서 확인하실 수 있습니다.

⏰ **알림 설정**: 복용 15분 전과 5분 전에 알림이 울립니다.

⚠️ **중요**: 정확한 복용을 위해 의사나 약사의 지시를 우선으로 따르세요.
"""
                
                # 생성된 이벤트 정보 추가
                if result.get('created_events'):
                    success_message += "\n📋 **추가된 일정들:**\n"
                    for event in result['created_events'][:3]:  # 처음 3개만 표시
                        success_message += f"- {event['summary']}\n"
                    
                    if len(result['created_events']) > 3:
                        success_message += f"- ... 외 {len(result['created_events']) - 3}개 더\n"
                
                return success_message
            else:
                return f"""
❌ **캘린더 추가 실패**

{result['message']}

다음을 확인해 주세요:
1. Google 계정 로그인 상태
2. Calendar 접근 권한 허용
3. 인터넷 연결 상태

다시 시도하시거나 관리자에게 문의해 주세요.
"""
        
        except Exception as e:
            # 세션 정리
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            return f"""
❌ **캘린더 추가 중 오류 발생**

오류: {str(e)}

잠시 후 다시 시도하시거나 관리자에게 문의해 주세요.
"""
    
    def handle_calendar_request(self, query: str, user_id: str = "default", user_context: dict = None) -> str:
        """캘린더 요청 통합 처리"""
        
        # 현재 확인 대기 중인 세션이 있는지 확인
        if user_id in self.user_sessions and self.user_sessions[user_id]['status'] == 'pending_confirmation':
            return self.check_confirmation(query, user_id)
        
        # 새로운 복약 정보 분석
        return self.analyze_medication_schedule(query, user_id, user_context)
    
    def get_upcoming_schedules(self, days: int = 7) -> str:
        """다가오는 복약 일정 조회"""
        try:
            events = calendar_agent.get_upcoming_medication_events(days)
            
            if not events:
                return f"앞으로 {days}일간 예정된 복약 알림이 없습니다."
            
            schedule_text = f"📅 **앞으로 {days}일간의 복약 일정** ({len(events)}개)\n\n"
            
            for i, event in enumerate(events[:10], 1):  # 최대 10개만 표시
                start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                formatted_time = start_time.strftime('%m월 %d일 %H:%M')
                
                schedule_text += f"{i}. **{event['summary']}**\n"
                schedule_text += f"   📅 {formatted_time}\n\n"
            
            if len(events) > 10:
                schedule_text += f"... 외 {len(events) - 10}개 더 있습니다.\n"
            
            schedule_text += "\n💡 Google Calendar에서 전체 일정을 확인하실 수 있습니다."
            
            return schedule_text
            
        except Exception as e:
            return f"복약 일정 조회 중 오류가 발생했습니다: {str(e)}"


# 싱글톤 인스턴스
calendar_ai = CalendarAI()