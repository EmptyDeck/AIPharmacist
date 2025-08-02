"""
IBM watsonx 클라이언트 유틸리티
의료 챗봇을 위한 watsonx AI 연결 및 응답 생성 기능
"""

import streamlit as st
from ibm_watson import WatsonxV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from typing import Optional, Dict, List, Any
import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WatsonxClient:
    """IBM watsonx 클라이언트 래퍼 클래스"""
    
    def __init__(self, api_key: str, service_url: str, project_id: str = None):
        """
        WatsonxClient 초기화
        
        Args:
            api_key: IBM Cloud API 키
            service_url: watsonx 서비스 URL
            project_id: 프로젝트 ID (선택사항)
        """
        self.api_key = api_key
        self.service_url = service_url
        self.project_id = project_id
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """watsonx 클라이언트 설정"""
        try:
            authenticator = IAMAuthenticator(self.api_key)
            self.client = WatsonxV1(
                version='2023-05-29',
                authenticator=authenticator
            )
            self.client.set_service_url(self.service_url)
            logger.info("watsonx 클라이언트 설정 완료")
        except Exception as e:
            logger.error(f"watsonx 클라이언트 설정 실패: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.client is not None
    
    def generate_text(
        self, 
        prompt: str, 
        model_id: str = "meta-llama/llama-2-70b-chat",
        max_tokens: int = 500,
        temperature: float = 0.3,
        top_p: float = 1.0
    ) -> str:
        """
        텍스트 생성
        
        Args:
            prompt: 입력 프롬프트
            model_id: 사용할 모델 ID
            max_tokens: 최대 토큰 수
            temperature: 창의성 수준 (0-1)
            top_p: 토큰 선택 확률 임계값
            
        Returns:
            생성된 텍스트
        """
        if not self.is_connected():
            logger.error("watsonx 클라이언트가 연결되지 않음")
            return "AI 서비스에 연결할 수 없습니다."
        
        try:
            response = self.client.generate(
                model_id=model_id,
                inputs=[prompt],
                parameters={
                    'decoding_method': 'greedy' if temperature == 0 else 'sample',
                    'max_new_tokens': max_tokens,
                    'temperature': temperature,
                    'top_p': top_p,
                    'repetition_penalty': 1.1
                }
            )
            
            if response and 'results' in response and response['results']:
                generated_text = response['results'][0]['generated_text']
                logger.info(f"텍스트 생성 성공 (길이: {len(generated_text)})")
                return generated_text.strip()
            else:
                logger.warning("응답에서 생성된 텍스트를 찾을 수 없음")
                return "응답 생성에 실패했습니다."
                
        except Exception as e:
            logger.error(f"텍스트 생성 중 오류: {e}")
            return f"텍스트 생성 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_medical_text(self, medical_text: str, patient_info: Dict = None) -> str:
        """
        의료 텍스트 분석 및 설명
        
        Args:
            medical_text: 분석할 의료 텍스트
            patient_info: 환자 정보 딕셔너리
            
        Returns:
            분석 결과 텍스트
        """
        # 환자 정보 추가
        patient_context = ""
        if patient_info:
            patient_context = f"""
환자 정보:
- 나이: {patient_info.get('age', '미상')}세
- 성별: {patient_info.get('gender', '미상')}
- 기저질환: {', '.join(patient_info.get('conditions', []))}
"""
        
        prompt = f"""
당신은 20년 경력의 가정의학과 전문의입니다.
다음 의료 텍스트를 분석하여 환자와 보호자가 이해하기 쉽게 설명해주세요.

{patient_context}

의료 텍스트:
{medical_text}

다음 형식으로 설명해주세요:
📋 **주요 진단**: (의학용어를 쉬운 말로 설명)
💊 **처방 약물**: (약물명과 효능을 간단히)
⚠️ **주의사항**: (중요한 주의점들)
🏥 **추천사항**: (생활습관, 재방문 등)

의학용어는 반드시 괄호 안에 쉬운 말로 설명하고, 따뜻하고 안심시키는 톤으로 작성하세요.
"""
        
        return self.generate_text(prompt, temperature=0.3)
    
    def generate_medical_advice(
        self, 
        question: str, 
        medical_context: str = "",
        drug_info: str = "",
        interactions: List[str] = None
    ) -> str:
        """
        의료 상담 조언 생성
        
        Args:
            question: 환자 질문
            medical_context: 의료 컨텍스트
            drug_info: 약물 정보
            interactions: 상호작용 경고 리스트
            
        Returns:
            의료 조언 텍스트
        """
        interaction_text = ""
        if interactions:
            interaction_text = f"""
⚠️ **약물 상호작용 경고**:
{chr(10).join(interactions)}
"""
        
        prompt = f"""
당신은 친절하고 경험이 풍부한 가정의학과 의사입니다.
환자의 질문에 대해 정확하고 이해하기 쉽게 답변해주세요.

의료 배경 정보:
{medical_context}

약물 정보:
{drug_info}

{interaction_text}

환자 질문: {question}

답변 시 다음 원칙을 지켜주세요:
1. 의학용어는 괄호 안에 쉬운 말로 설명
2. 중요한 주의사항은 ⚠️로 표시
3. 복용방법은 📋로 단계별 설명
4. 따뜻하고 안심시키는 톤 사용
5. 마지막에 "정확한 진단은 의사와 상담하세요" 포함

환자가 안심할 수 있도록 친근하게 답변해주세요.
"""
        
        return self.generate_text(prompt, temperature=0.4)

# 편의 함수들
def setup_watsonx_client() -> Optional[WatsonxClient]:
    """Streamlit 환경에서 watsonx 클라이언트 설정"""
    try:
        api_key = st.secrets.get("WATSONX_API_KEY")
        service_url = st.secrets.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        project_id = st.secrets.get("WATSONX_PROJECT_ID")
        
        if not api_key:
            st.warning("watsonx API 키가 설정되지 않았습니다.")
            return None
        
        client = WatsonxClient(api_key, service_url, project_id)
        
        if client.is_connected():
            st.success("watsonx 연결 성공! ✅")
            return client
        else:
            st.error("watsonx 연결 실패 ❌")
            return None
            
    except Exception as e:
        st.error(f"watsonx 설정 중 오류: {e}")
        return None

def generate_response(prompt: str, client: WatsonxClient = None) -> str:
    """간단한 응답 생성 함수"""
    if client and client.is_connected():
        return client.generate_text(prompt)
    else:
        return "AI 서비스에 연결할 수 없습니다. API 키를 확인해주세요."

def analyze_medical_text(text: str, patient_info: Dict = None, client: WatsonxClient = None) -> str:
    """의료 텍스트 분석 함수"""
    if client and client.is_connected():
        return client.analyze_medical_text(text, patient_info)
    else:
        return "의료 텍스트 분석을 위해 AI 서비스 연결이 필요합니다."

# 의료 전용 프롬프트 템플릿들
class MedicalPrompts:
    """의료 상담용 프롬프트 템플릿 모음"""
    
    SYSTEM_PROMPT = """
당신은 20년 경력의 가정의학과 전문의입니다.
환자와 보호자가 의학 정보를 쉽게 이해할 수 있도록 설명하는 것이 전문입니다.

기본 원칙:
1. 의학용어는 항상 괄호 안에 쉬운 말로 설명
2. 위험한 상황은 ⚠️ 표시로 강조
3. 복용법은 📋 단계별로 명확히 설명
4. 따뜻하고 안심시키는 톤 유지
5. 반드시 "의사와 상담 필요" 문구 포함
"""
    
    DRUG_EXPLANATION = """
다음 약물에 대해 환자가 이해하기 쉽게 설명해주세요:

약물명: {drug_name}
효능: {efficacy}
복용법: {usage}
주의사항: {warnings}

환자 정보: {patient_info}

📋 **이 약은 무엇인가요?**
💊 **어떻게 복용하나요?**
⚠️ **주의할 점은?**
🤔 **자주 묻는 질문**
"""
    
    INTERACTION_WARNING = """
다음 약물 조합에 대한 상호작용을 확인하고 주의사항을 설명해주세요:

현재 복용 약물: {current_drugs}
기저질환: {conditions}

⚠️ 위험도가 높은 조합이 있다면 명확히 경고하고,
안전한 대안이 있다면 제시해주세요.
"""