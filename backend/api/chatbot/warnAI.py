import httpx
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from core.config import settings
from typing import Optional


class WarnAI:
    """약물 안전성 및 경고 정보를 위한 전문 AI 에이전트"""
    
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
    
    def check_safety_warnings(self, query: str, user_context: dict = None) -> str:
        """약물 안전성 및 부작용에 대한 경고 정보를 제공합니다"""
        
        context_text = ""
        if user_context:
            if user_context.get('underlying_diseases'):
                context_text += f"기저질환: {', '.join(user_context['underlying_diseases'])}\n"
            if user_context.get('currentMedications'):
                context_text += f"현재 복용약물: {', '.join(user_context['currentMedications'])}\n"
        
        prompt = f"""
당신은 약물 안전성 전문가입니다. 다음 지침에 따라 약물의 안전성과 경고사항을 설명해주세요:

지침:
1. 심각한 부작용이나 응급상황 징후가 있다면 즉시 응급실 방문을 권하세요
2. 약물 상호작용의 위험성을 자세히 설명하세요
3. 특정 질환자가 피해야 할 약물이라면 명확히 경고하세요
4. 임신, 수유 중 안전성에 대해 언급하세요
5. 과량 복용 시 나타날 수 있는 증상을 설명하세요
6. 복용 중단 시 주의사항이 있다면 알려주세요
7. 반드시 "응급상황이 의심되면 즉시 119에 신고하거나 응급실로 가세요"를 포함하세요

환자 정보:
{context_text}

질문: {query}

위 정보를 바탕으로 약물의 안전성과 주의사항을 상세히 설명해주세요:
"""
        
        try:
            model = self.get_model()
            response = model.generate(
                prompt=prompt,
                params={
                    GenParams.MAX_NEW_TOKENS: 400,
                    GenParams.TEMPERATURE: 0.1,  # 안전 정보는 매우 보수적으로
                    GenParams.REPETITION_PENALTY: 1.1
                }
            )
            return response['results'][0]['generated_text'].strip()
        except Exception as e:
            return f"안전성 정보 조회 중 오류가 발생했습니다. 즉시 의료진과 상담하시기 바랍니다. 응급상황이라면 119에 신고하세요. 오류: {str(e)}"


# 싱글톤 인스턴스
warn_ai = WarnAI()