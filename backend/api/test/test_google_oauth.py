"""
Google OAuth 및 Calendar API 테스트 스크립트
모든 기능을 한 파일에서 테스트해볼 수 있습니다.
"""

import requests
import json
import webbrowser
from datetime import datetime, timedelta
import urllib.parse

class GoogleOAuthTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.user_id = "test_user_123"  # 테스트용 사용자 ID
        
    def print_section(self, title):
        print(f"\n{'='*50}")
        print(f"🔍 {title}")
        print('='*50)
        
    def print_result(self, success, message, data=None):
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}: {message}")
        if data:
            print(f"📄 응답 데이터: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("-" * 30)

    def test_1_oauth_login_flow(self):
        """1단계: OAuth 로그인 플로우 테스트"""
        self.print_section("1단계: OAuth 로그인 플로우 테스트")
        
        print("🌐 브라우저가 자동으로 열립니다...")
        print("Google 계정으로 로그인하고 권한을 승인해주세요.")
        print("승인 완료 후 이 스크립트로 돌아와서 Enter를 눌러주세요.")
        
        # 로그인 URL 생성
        login_url = f"{self.base_url}/auth/google/login-enhanced"
        
        try:
            response = requests.get(login_url)
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get('authorization_url')
                
                self.print_result(True, "로그인 URL 생성 성공", data)
                
                # 브라우저 자동 열기
                webbrowser.open(auth_url)
                
                # 사용자 입력 대기
                input("\n👆 브라우저에서 Google 로그인을 완료한 후 Enter를 눌러주세요...")
                
                return True
            else:
                self.print_result(False, f"로그인 URL 생성 실패 (상태코드: {response.status_code})", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"요청 실패: {str(e)}")
            return False

    def test_2_check_authenticated_users(self):
        """2단계: 인증된 사용자 목록 확인"""
        self.print_section("2단계: 인증된 사용자 확인")
        
        try:
            url = f"{self.base_url}/auth/users/list"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                user_count = data.get('authenticated_users_count', 0)
                
                if user_count > 0:
                    self.print_result(True, f"{user_count}명의 사용자가 인증되어 있습니다", data)
                    # 첫 번째 사용자를 테스트용으로 사용
                    if data.get('users'):
                        self.user_id = data['users'][0]
                        print(f"🎯 테스트 사용자 ID: {self.user_id}")
                    return True
                else:
                    self.print_result(False, "인증된 사용자가 없습니다. 먼저 OAuth 로그인을 완료해주세요.")
                    return False
            else:
                self.print_result(False, f"사용자 목록 조회 실패 (상태코드: {response.status_code})", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"요청 실패: {str(e)}")
            return False

    def test_3_create_calendar_event(self):
        """3단계: 캘린더 일정 생성 테스트"""
        self.print_section("3단계: 캘린더 일정 생성 테스트")
        
        # 테스트용 일정 데이터
        now = datetime.now()
        start_time = now + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)
        
        event_data = {
            "user_id": self.user_id,
            "medication_text": "타이레놀 500mg을 하루에 3번, 식후 30분에 복용",
            "start_date": start_time.isoformat()
        }
        
        try:
            url = f"{self.base_url}/api/calendar/add-medication"
            response = requests.post(url, json=event_data)
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, "캘린더 일정 생성 성공", data)
                
                # Google Calendar에서 확인할 수 있는 링크 제공
                if 'event_url' in data:
                    print(f"🌐 Google Calendar에서 확인: {data['event_url']}")
                
                return True
            else:
                self.print_result(False, f"일정 생성 실패 (상태코드: {response.status_code})", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"요청 실패: {str(e)}")
            return False

    def test_4_token_management(self):
        """4단계: 토큰 관리 테스트"""
        self.print_section("4단계: 토큰 관리 테스트")
        
        # 토큰 파일 확인
        import os
        token_file = f"user_tokens/google_token_{self.user_id}.json"
        
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                
                self.print_result(True, f"토큰 파일 발견: {token_file}")
                
                # 토큰 정보 출력 (민감한 정보는 마스킹)
                masked_data = {
                    "user_id": token_data.get("user_id"),
                    "token": token_data.get("token", "")[:10] + "..." if token_data.get("token") else None,
                    "refresh_token": "존재함" if token_data.get("refresh_token") else "없음",
                    "scopes": token_data.get("scopes", [])
                }
                
                print(f"📋 토큰 정보: {json.dumps(masked_data, indent=2, ensure_ascii=False)}")
                
                return True
                
            except Exception as e:
                self.print_result(False, f"토큰 파일 읽기 실패: {str(e)}")
                return False
        else:
            self.print_result(False, f"토큰 파일이 없습니다: {token_file}")
            return False

    def test_5_calendar_agent_direct(self):
        """5단계: Calendar Agent 직접 테스트"""
        self.print_section("5단계: Calendar Agent 직접 테스트")
        
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from utils.googleCalender.cal_agent import GoogleCalendarAgent
            
            agent = GoogleCalendarAgent()
            
            # 사용자 인증 상태 확인
            is_auth = agent.is_user_authenticated(self.user_id)
            
            if is_auth:
                self.print_result(True, f"사용자 {self.user_id} 인증 상태 확인됨")
                
                # 직접 일정 생성 테스트
                event_data = {
                    "summary": "🧪 Direct Agent 테스트",
                    "description": "Calendar Agent를 직접 호출한 테스트입니다.",
                    "start": {
                        "dateTime": (datetime.now() + timedelta(hours=2)).isoformat(),
                        "timeZone": "Asia/Seoul"
                    },
                    "end": {
                        "dateTime": (datetime.now() + timedelta(hours=2, minutes=30)).isoformat(),  
                        "timeZone": "Asia/Seoul"
                    }
                }
                
                result = agent.create_event(self.user_id, event_data)
                
                if result:
                    self.print_result(True, "Direct Agent로 일정 생성 성공", result)
                    return True
                else:
                    self.print_result(False, "Direct Agent로 일정 생성 실패")
                    return False
            else:
                self.print_result(False, f"사용자 {self.user_id} 인증되지 않음")
                return False
                
        except Exception as e:
            self.print_result(False, f"Calendar Agent 테스트 실패: {str(e)}")
            return False

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Google OAuth 및 Calendar API 전체 테스트 시작")
        print(f"📍 서버 주소: {self.base_url}")
        print(f"👤 테스트 사용자 ID: {self.user_id}")
        
        tests = [
            ("OAuth 로그인 플로우", self.test_1_oauth_login_flow),
            ("인증된 사용자 확인", self.test_2_check_authenticated_users),
            ("캘린더 일정 생성", self.test_3_create_calendar_event),
            ("토큰 관리 확인", self.test_4_token_management),
            ("Calendar Agent 직접 테스트", self.test_5_calendar_agent_direct)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 테스트 중 예외 발생: {str(e)}")
                results.append((test_name, False))
        
        # 최종 결과 요약
        self.print_section("🏁 테스트 결과 요약")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"📊 전체 테스트: {total}개")
        print(f"✅ 성공: {passed}개")
        print(f"❌ 실패: {total - passed}개")
        print(f"📈 성공률: {passed/total*100:.1f}%")
        
        print("\n📋 상세 결과:")
        for test_name, result in results:
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        if passed == total:
            print("\n🎉 모든 테스트가 성공했습니다!")
        else:
            print(f"\n⚠️  {total - passed}개의 테스트가 실패했습니다. 로그를 확인해주세요.")


def main():
    """메인 함수"""
    print("🔧 Google OAuth 테스트 도구")
    print("=" * 50)
    
    # 서버 주소 입력받기
    server_url = input("서버 주소를 입력하세요 (기본값: http://localhost:8001): ").strip()
    if not server_url:
        server_url = "http://localhost:8001"
    
    # 테스터 인스턴스 생성
    tester = GoogleOAuthTester(server_url)
    
    # 테스트 모드 선택
    print("\n테스트 모드를 선택하세요:")
    print("1. 전체 테스트 실행")
    print("2. 개별 테스트 선택")
    
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "1":
        tester.run_all_tests()
    elif choice == "2":
        tests = [
            ("OAuth 로그인 플로우", tester.test_1_oauth_login_flow),
            ("인증된 사용자 확인", tester.test_2_check_authenticated_users),
            ("캘린더 일정 생성", tester.test_3_create_calendar_event),
            ("토큰 관리 확인", tester.test_4_token_management),
            ("Calendar Agent 직접 테스트", tester.test_5_calendar_agent_direct)
        ]
        
        print("\n개별 테스트 목록:")
        for i, (test_name, _) in enumerate(tests, 1):
            print(f"{i}. {test_name}")
        
        try:
            test_num = int(input("테스트 번호를 선택하세요: ")) - 1
            if 0 <= test_num < len(tests):
                test_name, test_func = tests[test_num]
                print(f"\n🚀 {test_name} 테스트 시작")
                result = test_func()
                print(f"\n결과: {'성공' if result else '실패'}")
            else:
                print("잘못된 테스트 번호입니다.")
        except ValueError:
            print("숫자를 입력해주세요.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()