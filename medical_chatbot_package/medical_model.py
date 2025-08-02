"""
의료 챗봇 모델 클래스
백엔드 팀에서 import해서 사용할 수 있는 독립적인 모델 API
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging
import os
from pathlib import Path

# watsonx 클라이언트 (선택적 import)
try:
    from utils.watsonx_client import WatsonxClient
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False
    print("Warning: watsonx_client not available. Using fallback mode.")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalChatbotModel:
    """
    의료 챗봇 모델 메인 클래스
    백엔드에서 이 클래스를 import해서 사용
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        모델 초기화
        
        Args:
            config: 설정 딕셔너리
                - watsonx_api_key: IBM watsonx API 키
                - watsonx_url: watsonx 서비스 URL
                - data_path: 데이터 파일 경로
        """
        self.config = config or {}
        self.drug_database = []
        self.watsonx_client = None
        
        # 데이터 로드
        self._load_drug_database()
        
        # AI 클라이언트 초기화
        self._init_ai_client()
        
        logger.info("MedicalChatbotModel 초기화 완료")
    
    def _load_drug_database(self):
        """약물 데이터베이스 로드"""
        try:
            data_path = self.config.get('data_path', 'data/drug_data.csv')
            
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                self.drug_database = df.to_dict('records')
                logger.info(f"약물 데이터 로드 완료: {len(self.drug_database)}개")
            else:
                # 기본 데이터 사용
                self.drug_database = self._get_default_drug_data()
                logger.info("기본 약물 데이터 사용")
                
        except Exception as e:
            logger.error(f"약물 데이터 로드 실패: {e}")
            self.drug_database = self._get_default_drug_data()
    
    def _get_default_drug_data(self) -> List[Dict]:
        """기본 약물 데이터"""
        return [
            {
                "약품명": "타이레놀정500mg",
                "제조회사": "한국얀센",
                "주성분": "아세트아미노펜",
                "효능": "해열진통",
                "용법용량": "성인 1회 1-2정 1일 3-4회",
                "주의사항": "간질환 환자 주의",
                "상호작용": "알코올과 병용 금지",
                "부작용": "위장장애 드물게 발생"
            },
            {
                "약품명": "낙센정",
                "제조회사": "동아제약", 
                "주성분": "나프록센",
                "효능": "소염진통",
                "용법용량": "성인 1회 1정 1일 2회 식후복용",
                "주의사항": "위궤양 환자 금기",
                "상호작용": "와파린과 상호작용",
                "부작용": "위장장애, 복통"
            }
        ]
    
    def _init_ai_client(self):
        """AI 클라이언트 초기화"""
        if not WATSONX_AVAILABLE:
            logger.warning("watsonx 모듈 없음 - 기본 모드로 실행")
            return
            
        api_key = self.config.get('watsonx_api_key')
        service_url = self.config.get('watsonx_url', 'https://us-south.ml.cloud.ibm.com')
        
        if api_key:
            try:
                self.watsonx_client = WatsonxClient(api_key, service_url)
                if self.watsonx_client.is_connected():
                    logger.info("watsonx AI 클라이언트 연결 성공")
                else:
                    logger.warning("watsonx 연결 실패 - 기본 모드로 실행")
            except Exception as e:
                logger.error(f"watsonx 초기화 실패: {e}")
        else:
            logger.info("watsonx API 키 없음 - 기본 모드로 실행")
    
    # ===== 백엔드 연동용 메인 API 메서드들 =====
    
    def search_drugs(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        약물 검색
        
        Args:
            query: 검색어
            limit: 최대 결과 수
            
        Returns:
            {
                "success": bool,
                "data": List[Dict],
                "count": int,
                "timestamp": str
            }
        """
        try:
            results = []
            query_lower = query.lower()
            
            for drug in self.drug_database:
                if (query_lower in drug.get('약품명', '').lower() or
                    query_lower in drug.get('주성분', '').lower() or
                    query_lower in drug.get('효능', '').lower()):
                    
                    # 표준화된 형태로 변환
                    standardized_drug = {
                        "name": drug.get('약품명', ''),
                        "company": drug.get('제조회사', ''),
                        "ingredient": drug.get('주성분', ''),
                        "efficacy": drug.get('효능', ''),
                        "usage": drug.get('용법용량', ''),
                        "warnings": drug.get('주의사항', ''),
                        "interactions": drug.get('상호작용', ''),
                        "side_effects": drug.get('부작용', '')
                    }
                    results.append(standardized_drug)
                    
                    if len(results) >= limit:
                        break
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"약물 검색 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_drug_interactions(self, drugs: List[str], conditions: List[str] = None) -> Dict[str, Any]:
        """
        약물 상호작용 체크
        
        Args:
            drugs: 약물 리스트
            conditions: 기저질환 리스트
            
        Returns:
            {
                "success": bool,
                "data": {
                    "interactions": List[str],
                    "risk_level": str
                },
                "timestamp": str
            }
        """
        try:
            warnings = []
            
            # 위험한 약물 조합
            dangerous_combinations = {
                '와파린': ['아스피린', '타이레놀', '이부프로펜'],
                '디곡신': ['푸로세마이드'],
                '메트포르민': ['조영제']
            }
            
            # 약물-약물 상호작용 체크
            for i, drug1 in enumerate(drugs):
                for j, drug2 in enumerate(drugs):
                    if i != j:
                        for dangerous_drug, interactions in dangerous_combinations.items():
                            if dangerous_drug in drug1 and any(inter in drug2 for inter in interactions):
                                warnings.append(f"⚠️ {drug1}과 {drug2} 동시 복용 주의")
            
            # 기저질환-약물 상호작용
            if conditions:
                condition_warnings = {
                    '간질환': ['타이레놀', '아세트아미노펜'],
                    '신장질환': ['이부프로펜', '메트포르민'],
                    '위궤양': ['아스피린', '이부프로펜']
                }
                
                for condition in conditions:
                    if condition in condition_warnings:
                        for drug in drugs:
                            for warning_drug in condition_warnings[condition]:
                                if warning_drug in drug:
                                    warnings.append(f"⚠️ {condition} 환자는 {drug} 주의 필요")
            
            # 위험도 계산
            risk_level = "high" if len(warnings) > 2 else "medium" if warnings else "low"
            
            return {
                "success": True,
                "data": {
                    "interactions": list(set(warnings)),  # 중복 제거
                    "drugs_checked": drugs,
                    "conditions_considered": conditions or [],
                    "risk_level": risk_level
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"상호작용 체크 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_medical_note(self, note_text: str, patient_info: Dict = None) -> Dict[str, Any]:
        """
        의료 소견서 분석
        
        Args:
            note_text: 의료 소견서 텍스트
            patient_info: 환자 정보 딕셔너리
            
        Returns:
            {
                "success": bool,
                "data": {
                    "analysis": str,
                    "confidence": float
                },
                "timestamp": str
            }
        """
        try:
            if self.watsonx_client and self.watsonx_client.is_connected():
                # AI 분석 사용
                analysis = self.watsonx_client.analyze_medical_text(note_text, patient_info)
                confidence = 0.85
            else:
                # 규칙 기반 분석
                analysis = self._analyze_note_basic(note_text, patient_info)
                confidence = 0.6
            
            return {
                "success": True,
                "data": {
                    "analysis": analysis,
                    "original_note": note_text,
                    "patient_info": patient_info or {},
                    "confidence": confidence
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"소견서 분석 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_consultation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        의료 상담 생성 (메인 기능)
        
        Args:
            request: {
                "patient_info": Dict,
                "question": str,
                "medical_note": str,
                "current_drugs": List[str]
            }
            
        Returns:
            {
                "success": bool,
                "data": {
                    "advice": str,
                    "confidence": float,
                    "interactions": Dict
                },
                "timestamp": str
            }
        """
        try:
            patient_info = request.get('patient_info', {})
            question = request.get('question', '')
            medical_note = request.get('medical_note', '')
            current_drugs = request.get('current_drugs', [])
            
            # AI 상담 생성
            if self.watsonx_client and self.watsonx_client.is_connected():
                advice = self.watsonx_client.generate_medical_advice(
                    question=question,
                    medical_context=medical_note,
                    drug_info=str(current_drugs)
                )
                confidence = 0.85
            else:
                advice = self._generate_basic_advice(question, current_drugs, patient_info)
                confidence = 0.6
            
            # 상호작용 체크
            interactions = self.check_drug_interactions(
                current_drugs, 
                patient_info.get('conditions', [])
            )
            
            return {
                "success": True,
                "data": {
                    "advice": advice,
                    "patient_info": patient_info,
                    "question": question,
                    "interactions": interactions.get('data', {}),
                    "confidence": confidence,
                    "consultation_id": f"consult_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"상담 생성 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_note_basic(self, note_text: str, patient_info: Dict = None) -> str:
        """기본 소견서 분석 (AI 없이)"""
        analysis = "📋 **소견서 분석 결과**\n\n"
        
        # 키워드 기반 분석
        keywords = {
            "고혈압": "고혈압(혈압이 높은 상태) 관련 진료",
            "당뇨": "당뇨병 관련 진료", 
            "감기": "감기 또는 상기도 감염",
            "발열": "발열 증상",
            "통증": "통증 관리 필요",
            "처방": "약물 처방"
        }
        
        for keyword, description in keywords.items():
            if keyword in note_text:
                analysis += f"• {description}\n"
        
        analysis += "\n⚠️ **주의사항**: 정확한 진단은 의사와 상담하세요."
        return analysis
    
    def _generate_basic_advice(self, question: str, drugs: List[str], patient_info: Dict) -> str:
        """기본 상담 조언 생성 (AI 없이)"""
        advice = "안녕하세요! 다음과 같이 도움드릴 수 있습니다:\n\n"
        
        # 약물 관련 조언
        if drugs:
            advice += "💊 **복용 중인 약물에 대해**:\n"
            for drug_name in drugs[:3]:
                drug_info = self._find_drug_info(drug_name)
                if drug_info:
                    advice += f"• {drug_info['name']}: {drug_info['efficacy']}\n"
                    advice += f"  복용법: {drug_info['usage']}\n"
            advice += "\n"
        
        # 기저질환 조언
        conditions = patient_info.get('conditions', [])
        if conditions:
            advice += "⚠️ **기저질환 관련 주의사항**:\n"
            for condition in conditions:
                if condition == "고혈압":
                    advice += "• 염분 제한, 규칙적 운동 권장\n"
                elif condition == "당뇨병":
                    advice += "• 혈당 관리, 정기 검진 필요\n"
        
        advice += "\n🏥 **중요**: 정확한 진단과 치료는 반드시 의료진과 상담하세요."
        return advice
    
    def _find_drug_info(self, drug_name: str) -> Optional[Dict]:
        """약물 정보 찾기"""
        for drug in self.drug_database:
            if drug_name.lower() in drug.get('약품명', '').lower():
                return {
                    "name": drug.get('약품명', ''),
                    "efficacy": drug.get('효능', ''),
                    "usage": drug.get('용법용량', ''),
                    "warnings": drug.get('주의사항', '')
                }
        return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """모델 상태 확인"""
        return {
            "success": True,
            "data": {
                "model_name": "MedicalChatbotModel",
                "version": "1.0.0",
                "drug_database_size": len(self.drug_database),
                "ai_client_available": self.watsonx_client is not None,
                "ai_client_connected": (
                    self.watsonx_client.is_connected() 
                    if self.watsonx_client else False
                ),
                "capabilities": [
                    "drug_search",
                    "interaction_check", 
                    "medical_note_analysis",
                    "consultation_generation"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }

# ===== 백엔드 팀이 사용할 편의 함수들 =====

def create_medical_model(config: Dict[str, Any] = None) -> MedicalChatbotModel:
    """
    의료 모델 인스턴스 생성
    
    Args:
        config: 설정 딕셔너리
            - watsonx_api_key: IBM watsonx API 키
            - watsonx_url: watsonx 서비스 URL  
            - data_path: 데이터 파일 경로
    
    Returns:
        MedicalChatbotModel 인스턴스
    """
    return MedicalChatbotModel(config)

def quick_drug_search(query: str, api_key: str = None) -> Dict[str, Any]:
    """빠른 약물 검색"""
    config = {"watsonx_api_key": api_key} if api_key else {}
    model = create_medical_model(config)
    return model.search_drugs(query)

def quick_consultation(question: str, patient_info: Dict = None, api_key: str = None) -> Dict[str, Any]:
    """빠른 의료 상담"""
    config = {"watsonx_api_key": api_key} if api_key else {}
    model = create_medical_model(config)
    
    request = {
        "patient_info": patient_info or {},
        "question": question,
        "medical_note": "",
        "current_drugs": []
    }
    
    return model.generate_consultation(request)

# ===== 사용 예시 =====
if __name__ == "__main__":
    # 테스트 코드
    print("=== 의료 챗봇 모델 테스트 ===")
    
    # 모델 생성
    model = create_medical_model()
    
    # 상태 확인
    status = model.get_model_status()
    print("모델 상태:", status)
    
    # 약물 검색 테스트
    search_result = model.search_drugs("타이레놀")
    print("약물 검색:", search_result)
    
    # 상담 테스트
    consultation_request = {
        "patient_info": {"age": 30, "gender": "남성", "conditions": []},
        "question": "두통이 있을 때 타이레놀을 먹어도 되나요?",
        "medical_note": "",
        "current_drugs": ["타이레놀"]
    }
    
    consultation_result = model.generate_consultation(consultation_request)
    print("상담 결과:", consultation_result)