#!/usr/bin/env python3
"""
간단한 Google Calendar API 테스트 스크립트
실행만 하면 전체 OAuth 플로우를 자동으로 처리합니다.
"""

import requests
import webbrowser
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"🚧 {step_num}단계: {title}")
    print('='*60)

def print_result(success, message, data=None):
    status = "✅ 성공" if success else "❌ 실패"
    print(f"{status}: {message}")
    if data:
        print(f"📄 결과: {data}")
    print("-" * 40)

def step1_oauth_login():
    """1단계: OAuth 로그인 URL 받기"""
    print_step(1, "Google OAuth 로그인 시작")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/google/login-enhanced")
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('authorization_url')
            
            print_result(True, "로그인 URL 생성 완료")
            print(f"🌐 브라우저가 자동으로 열립니다...")
            print(f"🔗 URL: {auth_url[:80]}...")
            
            # 브라우저 자동 열기
            webbrowser.open(auth_url)
            
            # 사용자 입력 대기
            input("\n👆 브라우저에서 Google 로그인을 완료한 후 Enter를 눌러주세요...")
            return True
        else:
            print_result(False, f"로그인 URL 생성 실패 (상태코드: {response.status_code})")
            return False
    except Exception as e:
        print_result(False, f"요청 실패: {str(e)}")
        return False

def step2_check_users():
    """2단계: 인증된 사용자 확인"""
    print_step(2, "인증된 사용자 확인")
    
    try:
        response = requests.get(f"{BASE_URL}/auth/users/list")
        if response.status_code == 200:
            data = response.json()
            user_count = data.get('authenticated_users_count', 0)
            
            if user_count > 0:
                users = data.get('users', [])
                user_email = users[0]
                print_result(True, f"{user_count}명의 사용자가 인증되었습니다")
                print(f"🎯 사용자: {user_email}")
                return user_email
            else:
                print_result(False, "인증된 사용자가 없습니다. 1단계를 다시 확인해주세요.")
                return None
        else:
            print_result(False, f"사용자 목록 조회 실패 (상태코드: {response.status_code})")
            return None
    except Exception as e:
        print_result(False, f"요청 실패: {str(e)}")
        return None

def step3_create_calendar_event(user_email):
    """3단계: 캘린더 일정 생성"""
    print_step(3, "Google Calendar 일정 생성")
    
    # 테스트용 약물 정보들
    medications = [
        "비타민 D를 하루에 1번 아침에 복용",
        "오메가3를 하루에 2번 아침, 저녁에 복용", 
        "마그네슘을 하루에 3번 아침, 점심, 저녁에 복용"
    ]
    
    total_events = 0
    
    for i, medication_text in enumerate(medications, 1):
        try:
            start_date = (datetime.now() + timedelta(days=i)).isoformat()
            
            event_data = {
                "user_id": user_email,
                "medication_text": medication_text,
                "start_date": start_date
            }
            
            response = requests.post(f"{BASE_URL}/api/calendar/add-medication", json=event_data)
            
            if response.status_code == 200:
                data = response.json()
                events_added = data.get('events_added', 0)
                total_events += events_added
                
                print(f"✅ 테스트 {i}: {events_added}개 일정 추가 성공")
                print(f"   약물: {medication_text}")
                
                # 생성된 이벤트 정보 출력
                created_events = data.get('created_events', [])
                for event in created_events:
                    print(f"   📅 {event.get('summary')} - {event.get('start')}")
                    
            else:
                print(f"❌ 테스트 {i}: 일정 생성 실패 (상태코드: {response.status_code})")
                
        except Exception as e:
            print(f"❌ 테스트 {i}: 요청 실패 - {str(e)}")
    
    print_result(True, f"총 {total_events}개의 캘린더 일정이 생성되었습니다!")
    return total_events > 0

def step4_verify_calendar():
    """4단계: 캘린더 확인 안내"""
    print_step(4, "결과 확인")
    
    print("🎉 테스트 완료!")
    print("\n📋 확인 방법:")
    print("1. Google Calendar 웹사이트 방문: https://calendar.google.com")
    print("2. Google Calendar 모바일 앱 확인")
    print("3. 복약 알림은 💊 이모지로 표시됩니다")
    print("\n⏰ 설정된 알림:")
    print("- 복용 15분 전 팝업 알림")
    print("- 복용 5분 전 팝업 알림")
    
    print("\n✨ 주요 기능:")
    print("- AI 기반 복약 텍스트 파싱")
    print("- 자동 복용 시간 인식 (아침, 점심, 저녁)")
    print("- 반복 일정 자동 생성")
    print("- 중복 이벤트 방지")

def main():
    """메인 실행 함수"""
    print("🚀 Google Calendar API 자동 테스트 시작")
    print(f"📍 서버 주소: {BASE_URL}")
    print("\n⚠️  사전 준비사항:")
    print("1. Docker 컨테이너가 실행 중이어야 합니다")
    print("2. Google OAuth 설정이 완료되어야 합니다")
    print("3. IBM Watson API 키가 설정되어야 합니다")
    
    input("\n준비가 완료되었으면 Enter를 눌러주세요...")
    
    # 1단계: OAuth 로그인
    if not step1_oauth_login():
        print("❌ OAuth 로그인에 실패했습니다. 프로그램을 종료합니다.")
        return
    
    # 잠시 대기 (토큰 저장 시간)
    print("⏳ 토큰 저장 중... (3초 대기)")
    time.sleep(3)
    
    # 2단계: 사용자 확인
    user_email = step2_check_users()
    if not user_email:
        print("❌ 인증된 사용자를 찾을 수 없습니다. 프로그램을 종료합니다.")
        return
    
    # 3단계: 캘린더 일정 생성
    if step3_create_calendar_event(user_email):
        # 4단계: 결과 확인 안내
        step4_verify_calendar()
    else:
        print("❌ 캘린더 일정 생성에 실패했습니다.")
    
    print(f"\n🎯 완료! 총 소요시간: 약 1-2분")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {str(e)}")