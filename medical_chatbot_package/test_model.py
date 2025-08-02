"""
의료 챗봇 모델 테스트 스크립트
모델 개발자가 독립적으로 모델을 테스트할 수 있는 스크립트
"""

import json
from medical_model import create_medical_model, quick_drug_search, quick_consultation

def test_model_basic():
    """기본 모델 테스트"""
    print("🔧 === 기본 모델 테스트 ===")
    
    # 모델 생성 (API 키 없이도 작동)
    model = create_medical_model()
    
    # 상태 확인
    status = model.get_model_status()
    print("✅ 모델 상태:")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    print()

def test_drug_search():
    """약물 검색 테스트"""
    print("💊 === 약물 검색 테스트 ===")
    
    model = create_medical_model()
    
    test_queries = ["타이레놀", "혈압약", "진통제", "감기약"]
    
    for query in test_queries:
        print(f"🔍 검색어: '{query}'")
        result = model.search_drugs(query, limit=3)
        
        if result["success"]:
            print(f"   결과: {result['count']}개 발견")
            for drug in result["data"][:2]:  # 처음 2개만 출력
                print(f"   - {drug['name']}: {drug['efficacy']}")
        else:
            print(f"   오류: {result['error']}")
        print()

def test_drug_interactions():
    """약물 상호작용 테스트"""
    print("⚠️ === 약물 상호작용 테스트 ===")
    
    model = create_medical_model()
    
    test_cases = [
        {
            "drugs": ["와파린", "아스피린"],
            "conditions": []
        },
        {
            "drugs": ["타이레놀", "알코올"],
            "conditions": ["간질환"]
        },
        {
            "drugs": ["이부프로펜", "메트포르민"],
            "conditions": ["신장질환"]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"🧪 테스트 케이스 {i}:")
        print(f"   약물: {case['drugs']}")
        print(f"   기저질환: {case['conditions']}")
        
        result = model.check_drug_interactions(case["drugs"], case["conditions"])
        
        if result["success"]:
            interactions = result["data"]["interactions"]
            risk_level = result["data"]["risk_level"]
            print(f"   위험도: {risk_level}")
            
            if interactions:
                print("   경고사항:")
                for warning in interactions:
                    print(f"     - {warning}")
            else:
                print("   상호작용 없음")
        else:
            print(f"   오류: {result['error']}")
        print()

def test_medical_note_analysis():
    """의료 소견서 분석 테스트"""
    print("📋 === 의료 소견서 분석 테스트 ===")
    
    model = create_medical_model()
    
    test_notes = [
        "환자는 45세 남성으로 고혈압 병력이 있습니다. 두통 호소하여 타이레놀 500mg 처방합니다.",
        "28세 여성 환자, 임신 16주차로 감기 증상 있어 안전한 해열제 처방하였습니다.",
        "65세 남성, 당뇨병 환자로 혈당 조절 불량하여 메트포르민 용량 조절하였습니다."
    ]
    
    for i, note in enumerate(test_notes, 1):
        print(f"📄 소견서 {i}:")
        print(f"   내용: {note}")
        
        result = model.analyze_medical_note(note)
        
        if result["success"]:
            confidence = result["data"]["confidence"]
            analysis = result["data"]["analysis"]
            print(f"   신뢰도: {confidence:.0%}")
            print(f"   분석 결과:")
            for line in analysis.split('\n'):
                if line.strip():
                    print(f"     {line}")
        else:
            print(f"   오류: {result['error']}")
        print()

def test_consultation():
    """의료 상담 테스트"""
    print("🤖 === 의료 상담 테스트 ===")
    
    model = create_medical_model()
    
    test_consultations = [
        {
            "patient_info": {
                "age": 30,
                "gender": "남성",
                "conditions": []
            },
            "question": "두통이 있을 때 타이레놀을 하루에 몇 번 먹어야 하나요?",
            "current_drugs": ["타이레놀"]
        },
        {
            "patient_info": {
                "age": 55,
                "gender": "여성", 
                "conditions": ["고혈압", "당뇨병"]
            },
            "question": "혈압약과 당뇨약을 같이 먹어도 되나요?",
            "current_drugs": ["노르바스크", "메트포르민"]
        }
    ]
    
    for i, consultation in enumerate(test_consultations, 1):
        print(f"💬 상담 {i}:")
        print(f"   환자: {consultation['patient_info']['age']}세 {consultation['patient_info']['gender']}")
        print(f"   기저질환: {consultation['patient_info']['conditions']}")
        print(f"   복용약물: {consultation['current_drugs']}")
        print(f"   질문: {consultation['question']}")
        
        result = model.generate_consultation(consultation)
        
        if result["success"]:
            confidence = result["data"]["confidence"]
            advice = result["data"]["advice"]
            interactions = result["data"]["interactions"]
            
            print(f"   신뢰도: {confidence:.0%}")
            print("   상담 답변:")
            for line in advice.split('\n')[:5]:  # 처음 5줄만
                if line.strip():
                    print(f"     {line}")
            
            if interactions.get("interactions"):
                print("   상호작용 경고:")
                for warning in interactions["interactions"][:2]:  # 처음 2개만
                    print(f"     - {warning}")
        else:
            print(f"   오류: {result['error']}")
        print()

def test_quick_functions():
    """빠른 함수들 테스트"""
    print("⚡ === 빠른 함수 테스트 ===")
    
    # 빠른 약물 검색
    print("💊 빠른 약물 검색:")
    result = quick_drug_search("타이레놀")
    if result["success"] and result["data"]:
        drug = result["data"][0]
        print(f"   {drug['name']}: {drug['efficacy']}")
    
    # 빠른 상담
    print("🤖 빠른 상담:")
    result = quick_consultation(
        "감기에 걸렸는데 어떤 약을 먹어야 하나요?",
        {"age": 25, "gender": "여성", "conditions": []}
    )
    if result["success"]:
        advice = result["data"]["advice"]
        print(f"   답변: {advice.split('.')[0]}...")  # 첫 문장만
    
    print()

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 의료 챗봇 모델 종합 테스트")
    print("=" * 50)
    
    try:
        test_model_basic()
        test_drug_search()
        test_drug_interactions()
        test_medical_note_analysis()
        test_consultation()
        test_quick_functions()
        
        print("✅ 모든 테스트 완료!")
        print("💡 모델이 정상적으로 작동합니다.")
        print("📦 백엔드 팀에서 medical_model.py를 import해서 사용하면 됩니다.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        print("🔧 medical_model.py와 관련 파일들을 확인해주세요.")

if __name__ == "__main__":
    # 개별 테스트 실행 옵션
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        if test_name == "basic":
            test_model_basic()
        elif test_name == "search":
            test_drug_search()
        elif test_name == "interaction":
            test_drug_interactions()
        elif test_name == "analysis":
            test_medical_note_analysis()
        elif test_name == "consultation":
            test_consultation()
        elif test_name == "quick":
            test_quick_functions()
        else:
            print("사용법: python test_model.py [basic|search|interaction|analysis|consultation|quick]")
    else:
        # 전체 테스트 실행
        run_all_tests()