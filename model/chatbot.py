import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
from sentence_transformers import SentenceTransformer
import faiss
from dataclasses import dataclass
import re
import requests
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== 1. 데이터 구조 정의 =====
@dataclass
class MedicalDocument:
    """의료 문서 구조"""
    doc_id: str
    patient_id: str
    doc_type: str  # 'diagnosis', 'prescription', 'lab_result'
    content: str
    date: str
    icd_codes: List[str]
    medications: List[Dict]
    
@dataclass
class Drug:
    """약물 정보 구조"""
    drug_id: str
    name_kr: str
    name_en: str
    ingredients: List[str]
    category: str
    warnings: List[str]
    interactions: List[str]
    dosage_info: Dict

# ===== 2. 데이터 수집 및 전처리 =====
class MedicalDataCollector:
    """의료 데이터 수집 및 전처리 클래스"""
    
    def __init__(self):
        self.mfds_api_key = os.getenv('MFDS_API_KEY')
        self.hira_api_key = os.getenv('HIRA_API_KEY')
        
    def fetch_drug_info(self, drug_name: str) -> Dict:
        """식약처 API에서 약물 정보 조회"""
        url = "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService/getDrugPrdtPrmsnDtl"
        params = {
            'serviceKey': self.mfds_api_key,
            'itemName': drug_name,
            'type': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            return self._parse_drug_info(data)
        except Exception as e:
            logger.error(f"약물 정보 조회 실패: {e}")
            return {}
    
    def _parse_drug_info(self, data: Dict) -> Dict:
        """약물 정보 파싱"""
        # API 응답 구조에 따라 파싱 로직 구현
        parsed_info = {
            'name': data.get('ITEM_NAME', ''),
            'ingredients': data.get('MATERIAL_NAME', '').split(','),
            'company': data.get('ENTP_NAME', ''),
            'category': data.get('CLASS_NAME', ''),
            'warnings': self._extract_warnings(data.get('NB_DOC_DATA', ''))
        }
        return parsed_info
    
    def _extract_warnings(self, warning_text: str) -> List[str]:
        """경고 사항 추출"""
        warnings = []
        patterns = [
            r'주의사항.*?(?=\n\n|\Z)',
            r'부작용.*?(?=\n\n|\Z)',
            r'금기.*?(?=\n\n|\Z)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, warning_text, re.DOTALL)
            warnings.extend(matches)
        
        return warnings

# ===== 3. 의료 텍스트 전처리 =====
class MedicalTextPreprocessor:
    """의료 텍스트 전처리 클래스"""
    
    def __init__(self):
        self.medical_abbr = self._load_medical_abbreviations()
        self.drug_synonyms = self._load_drug_synonyms()
        
    def _load_medical_abbreviations(self) -> Dict:
        """의료 약어 사전 로드"""
        # 실제로는 파일에서 로드
        return {
            'HTN': '고혈압',
            'DM': '당뇨병',
            'CHF': '울혈성 심부전',
            'COPD': '만성폐쇄성폐질환'
        }
    
    def _load_drug_synonyms(self) -> Dict:
        """약물 동의어 사전 로드"""
        return {
            '타이레놀': ['아세트아미노펜', 'acetaminophen', 'paracetamol'],
            '부루펜': ['이부프로펜', 'ibuprofen'],
            '아스피린': ['aspirin', 'ASA']
        }
    
    def preprocess(self, text: str) -> str:
        """의료 텍스트 전처리"""
        # 약어 확장
        for abbr, full in self.medical_abbr.items():
            text = re.sub(rf'\b{abbr}\b', f'{abbr}({full})', text)
        
        # 약물명 표준화
        for standard, synonyms in self.drug_synonyms.items():
            for syn in synonyms:
                text = re.sub(rf'\b{syn}\b', standard, text, flags=re.IGNORECASE)
        
        # 숫자 + 단위 정규화
        text = re.sub(r'(\d+)\s*(mg|g|ml|cc)', r'\1\2', text)
        
        return text

# ===== 4. RAG 시스템 구현 =====
class MedicalRAGSystem:
    """의료 정보 검색 증강 생성 시스템"""
    
    def __init__(self, model_name: str = "monologg/kobigbird-bert-base"):
        self.encoder = SentenceTransformer('jhgan/ko-sroberta-multitask')
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.index = None
        self.documents = []
        
    def build_index(self, documents: List[str]):
        """문서 임베딩 및 인덱스 구축"""
        logger.info(f"인덱스 구축 시작: {len(documents)}개 문서")
        
        # 문서 임베딩
        embeddings = self.encoder.encode(documents)
        
        # FAISS 인덱스 구축
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        self.documents = documents
        
        logger.info("인덱스 구축 완료")
    
    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """관련 문서 검색"""
        query_embedding = self.encoder.encode([query])
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(distance)))
        
        return results

# ===== 5. 약물 상호작용 검증 시스템 =====
class DrugInteractionChecker:
    """약물 상호작용 검증 클래스"""
    
    def __init__(self):
        self.interaction_db = self._load_interaction_database()
        
    def _load_interaction_database(self) -> Dict:
        """약물 상호작용 데이터베이스 로드"""
        # 실제로는 DrugBank 데이터에서 로드
        return {
            ('와파린', '아스피린'): {
                'severity': 'major',
                'effect': '출혈 위험 증가',
                'recommendation': '용량 조절 필요, 주의 깊은 모니터링'
            },
            ('메트포르민', '조영제'): {
                'severity': 'major',
                'effect': '유산산증 위험',
                'recommendation': '조영제 사용 전후 48시간 메트포르민 중단'
            }
        }
    
    def check_interactions(self, medications: List[str]) -> List[Dict]:
        """약물 상호작용 검사"""
        interactions = []
        
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                drug1, drug2 = medications[i], medications[j]
                
                # 양방향 검사
                key1 = (drug1, drug2)
                key2 = (drug2, drug1)
                
                if key1 in self.interaction_db:
                    interaction = self.interaction_db[key1].copy()
                    interaction['drugs'] = [drug1, drug2]
                    interactions.append(interaction)
                elif key2 in self.interaction_db:
                    interaction = self.interaction_db[key2].copy()
                    interaction['drugs'] = [drug2, drug1]
                    interactions.append(interaction)
        
        return interactions

# ===== 6. 의료 챗봇 메인 클래스 =====
class MedicalChatbot:
    """의료 정보 제공 챗봇"""
    
    def __init__(self):
        # LLM 모델 초기화
        self.model_name = "beomi/KoAlpaca-Polyglot-5.8B"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # 구성 요소 초기화
        self.rag_system = MedicalRAGSystem()
        self.preprocessor = MedicalTextPreprocessor()
        self.drug_checker = DrugInteractionChecker()
        self.data_collector = MedicalDataCollector()
        
        # 프롬프트 템플릿
        self.prompt_template = """당신은 의료 정보를 쉽게 설명해주는 전문 의료 상담 AI입니다.
환자나 보호자가 이해하기 쉽도록 의학 용어를 풀어서 설명해주세요.

[관련 정보]
{context}

[환자 정보]
- 기저질환: {conditions}
- 복용 중인 약물: {medications}

[질문]
{question}

[답변]
"""
    
    def generate_response(self, 
                         question: str,
                         medical_document: str,
                         conditions: List[str] = [],
                         medications: List[str] = []) -> Dict:
        """질문에 대한 응답 생성"""
        
        # 1. 텍스트 전처리
        processed_doc = self.preprocessor.preprocess(medical_document)
        processed_question = self.preprocessor.preprocess(question)
        
        # 2. 관련 정보 검색
        relevant_docs = self.rag_system.retrieve(processed_question, k=3)
        context = "\n".join([doc[0] for doc in relevant_docs])
        
        # 3. 약물 상호작용 검사
        interactions = []
        if medications:
            interactions = self.drug_checker.check_interactions(medications)
        
        # 4. 프롬프트 구성
        prompt = self.prompt_template.format(
            context=context,
            conditions=", ".join(conditions) if conditions else "없음",
            medications=", ".join(medications) if medications else "없음",
            question=processed_question
        )
        
        # 5. 응답 생성
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        
        # 6. 결과 구성
        result = {
            'answer': response,
            'drug_interactions': interactions,
            'references': [doc[0][:100] + "..." for doc in relevant_docs],
            'confidence': self._calculate_confidence(relevant_docs)
        }
        
        # 7. 안전성 검증
        result['safety_warnings'] = self._check_safety(response, conditions, medications)
        
        return result
    
    def _calculate_confidence(self, relevant_docs: List[Tuple[str, float]]) -> float:
        """응답 신뢰도 계산"""
        if not relevant_docs:
            return 0.0
        
        # 거리 기반 신뢰도 계산 (낮을수록 좋음)
        avg_distance = np.mean([doc[1] for doc in relevant_docs])
        confidence = max(0, 1 - (avg_distance / 100))
        
        return round(confidence, 2)
    
    def _check_safety(self, response: str, conditions: List[str], medications: List[str]) -> List[str]:
        """안전성 경고 확인"""
        warnings = []
        
        # 당뇨 환자 주의사항
        if '당뇨' in conditions or 'DM' in conditions:
            if any(word in response for word in ['스테로이드', '프레드니솔론', '덱사메타손']):
                warnings.append("⚠️ 당뇨 환자의 경우 스테로이드 사용 시 혈당 상승 주의")
        
        # 임산부 주의사항
        if '임신' in conditions or '임산부' in response:
            dangerous_drugs = ['와파린', '메토트렉세이트', '이소트레티노인']
            if any(drug in response for drug in dangerous_drugs):
                warnings.append("⚠️ 임산부 금기 약물 포함 - 반드시 의사와 상담 필요")
        
        return warnings

# ===== 7. 학습 및 평가 시스템 =====
class MedicalModelTrainer:
    """의료 모델 학습 클래스"""
    
    def __init__(self, base_model: str):
        self.base_model = base_model
        self.training_data = []
        
    def prepare_training_data(self, data_path: str):
        """학습 데이터 준비"""
        # MIMIC-III 데이터 로드 및 전처리
        df = pd.read_csv(data_path)
        
        for _, row in df.iterrows():
            # 의료 문서를 Q&A 형식으로 변환
            document = row['text']
            
            # 자동 질문 생성
            questions = self._generate_questions(document)
            
            for q in questions:
                self.training_data.append({
                    'instruction': q,
                    'input': document,
                    'output': self._generate_answer(document, q)
                })
    
    def _generate_questions(self, document: str) -> List[str]:
        """문서에서 질문 자동 생성"""
        questions = []
        
        # 진단 관련 질문
        if '진단' in document:
            questions.append("이 진단은 무엇을 의미하나요?")
            questions.append("이 질환의 주요 증상은 무엇인가요?")
        
        # 약물 관련 질문
        if '처방' in document or 'mg' in document:
            questions.append("처방된 약물의 용도는 무엇인가요?")
            questions.append("이 약의 부작용은 어떤 것이 있나요?")
        
        return questions
    
    def _generate_answer(self, document: str, question: str) -> str:
        """질문에 대한 답변 생성 (학습용)"""
        # 실제로는 의료진이 검증한 답변 사용
        # 여기서는 간단한 규칙 기반 생성
        return f"문서 내용을 바탕으로 {question}에 대해 설명드리겠습니다..."

# ===== 8. 사용 예시 =====
def main():
    """메인 실행 함수"""
    
    # 챗봇 초기화
    chatbot = MedicalChatbot()
    
    # RAG 시스템에 의료 지식 색인
    medical_knowledge = [
        "당뇨병은 혈당이 정상보다 높은 상태가 지속되는 만성 질환입니다.",
        "고혈압은 혈압이 지속적으로 높은 상태로, 심혈관 질환의 주요 위험 요인입니다.",
        "아스피린은 혈소판 응집을 억제하여 혈전 형성을 예방하는 약물입니다.",
        # ... 더 많은 의료 지식
    ]
    chatbot.rag_system.build_index(medical_knowledge)
    
    # 사용자 입력 예시
    medical_document = """
    환자명: 홍길동 (65세, 남)
    진단: 제2형 당뇨병, 고혈압
    
    처방:
    1. 메트포르민 500mg - 1일 2회, 아침 저녁 식후
    2. 암로디핀 5mg - 1일 1회, 아침 식후
    
    주의사항: 규칙적인 운동과 식이조절 필요
    """
    
    question = "처방받은 약들을 함께 복용해도 안전한가요?"
    conditions = ["당뇨병", "고혈압"]
    medications = ["메트포르민", "암로디핀"]
    
    # 응답 생성
    response = chatbot.generate_response(
        question=question,
        medical_document=medical_document,
        conditions=conditions,
        medications=medications
    )
    
    # 결과 출력
    print("=" * 50)
    print(f"질문: {question}")
    print("=" * 50)
    print(f"답변: {response['answer']}")
    print(f"\n신뢰도: {response['confidence']}")
    
    if response['drug_interactions']:
        print("\n⚠️ 약물 상호작용 경고:")
        for interaction in response['drug_interactions']:
            print(f"- {interaction['drugs']}: {interaction['effect']}")
    
    if response['safety_warnings']:
        print("\n⚠️ 안전 주의사항:")
        for warning in response['safety_warnings']:
            print(f"- {warning}")

if __name__ == "__main__":
    main()