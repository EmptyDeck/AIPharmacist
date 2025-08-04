import httpx
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from core.config import settings
from typing import Optional


class ExplainAI:
    """약물 정보 설명을 위한 전문 AI 에이전트"""
    
    def __init__(self):
        self._model: Optional[Model] = None
    
    def get_model(self) -> Model:
        """IBM Watson 모델 인스턴스를 반환합니다"""
        if self._model is None:
            creds = {
                "url": settings.WATSONX_API_URL,
                "apikey": settings.WATSONX_API_KEY
            }
            self._model = Model(
                model_id='ibm/granite-3-3-8b-instruct',
                credentials=creds,
                project_id=settings.WATSONX_PROJECT_ID
            )
        return self._model
    
    def explain_medication(self, query: str, user_context: dict = None) -> str:
        """약물에 대한 상세한 설명을 제공합니다"""
        
        context_text = ""
        if user_context:
            if user_context.get('underlying_diseases'):
                context_text += f"기저질환: {', '.join(user_context['underlying_diseases'])}\n"
            if user_context.get('currentMedications'):
                context_text += f"현재 복용약물: {', '.join(user_context['currentMedications'])}\n"
        
        prompt = f"""
당신은 약물 정보 전문가입니다. 다음 지침에 따라 약물에 대해 상세히 설명해주세요:

지침:
1. 약물의 효능과 작용 메커니즘을 설명하세요
2. 일반적인 복용법과 주의사항을 알려주세요
3. 주요 부작용과 상호작용을 설명하세요
4. 복용 시 주의해야 할 음식이나 활동이 있다면 알려주세요
5. 반드시 "이는 일반적인 정보이며, 개인별 상황에 따라 다를 수 있으므로 반드시 의사나 약사와 상담하세요"라고 마무리하세요

환자 정보:
{context_text}

질문: {query}

위 정보를 바탕으로 약물에 대해 상세하고 정확한 설명을 제공해주세요:
"""
        
        try:
            model = self.get_model()
            response = model.generate(
                prompt=prompt,
                params={
                    GenParams.MAX_NEW_TOKENS: 400,
                    GenParams.TEMPERATURE: 0.2,  # 정확한 정보를 위해 낮은 온도
                    GenParams.REPETITION_PENALTY: 1.1
                }
            )
            return response['results'][0]['generated_text'].strip()
        except Exception as e:
            return f"약물 정보 조회 중 오류가 발생했습니다. 약사나 의사와 직접 상담하시기 바랍니다. 오류: {str(e)}"


# 싱글톤 인스턴스
explain_ai = ExplainAI()