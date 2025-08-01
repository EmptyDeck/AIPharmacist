import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import pickle
from tqdm import tqdm
import hashlib
from googletrans import Translator
import time

# ===== MIMIC-III 데이터 처리 =====
class MIMICDataProcessor:
    """MIMIC-III 데이터셋 처리 클래스"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.translator = Translator()
        self.translation_cache = {}
        
    def load_mimic_notes(self) -> pd.DataFrame:
        """MIMIC-III 임상 노트 로드"""
        notes_df = pd.read_csv(f"{self.data_path}/NOTEEVENTS.csv")
        
        # 필요한 카테고리만 필터링
        categories = ['Discharge summary', 'Physician', 'Nursing']
        filtered_notes = notes_df[notes_df['CATEGORY'].isin(categories)]
        
        return filtered_notes
    
    def translate_batch(self, texts: List[str], batch_size: int = 10) -> List[str]:
        """배치 번역 (API 제한 고려)"""
        translated_texts = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="번역 중"):
            batch = texts[i:i + batch_size]
            batch_translations = []
            
            for text in batch:
                # 캐시 확인
                text_hash = hashlib.md5(text.encode()).hexdigest()
                if text_hash in self.translation_cache:
                    batch_translations.append(self.translation_cache[text_hash])
                else:
                    try:
                        # 번역 (너무 긴 텍스트는 분할)
                        if len(text) > 5000:
                            chunks = [text[j:j+5000] for j in range(0, len(text), 5000)]
                            translated_chunks = []
                            for chunk in chunks:
                                trans = self.translator.translate(chunk, src='en', dest='ko')
                                translated_chunks.append(trans.text)
                                time.sleep(0.1)  # API 제한 회피
                            translated = ' '.join(translated_chunks)
                        else:
                            trans = self.translator.translate(text, src='en', dest='ko')
                            translated = trans.text
                        
                        self.translation_cache[text_hash] = translated
                        batch_translations.append(translated)
                        
                    except Exception as e:
                        logger.error(f"번역 실패: {e}")
                        batch_translations.append(text)  # 실패시 원문 사용
                    
                    time.sleep(0.5)  # API 제한 회피
            
            translated_texts.extend(batch_translations)
        
        # 캐시 저장
        with open('translation_cache.pkl', 'wb') as f:
            pickle.dump(self.translation_cache, f)
        
        return translated_texts
    
    def extract_medications(self, text: str) -> List[Dict]:
        """텍스트에서 약물 정보 추출"""
        medications = []
        
        # 약물 패턴 매칭
        med_patterns = [
            r'(\w+)\s+(\d+)\s*(mg|mcg|g|ml)',
            r'(\w+)\s+(\d+)-(\d+)\s*(mg|mcg|g|ml)',
        ]
        
        for pattern in med_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                medications.append({
                    'name': match[0],
                    'dosage': match[1],
                    'unit': match[-1]
                })
        
        return medications

# ===== 한국 의약품 데이터 수집 =====
class KoreanDrugDataCollector:
    """한국 의약품 데이터 수집기"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://apis.data.go.kr/1471000"
        
    async def fetch_all_drugs(self, page_size: int = 100) -> List[Dict]:
        """모든 의약품 정보 비동기 수집"""
        all_drugs = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                drugs = await self._fetch_page(session, page, page_size)
                if not drugs:
                    break
                all_drugs.extend(drugs)
                page += 1
                
                if page % 10 == 0:
                    logger.info(f"수집 진행 중: {len(all_drugs)}개 약물")
        
        return all_drugs
    
    async def _fetch_page(self, session: aiohttp.ClientSession, 
                         page: int, page_size: int) -> List[Dict]:
        """한 페이지 데이터 수집"""
        url = f"{self.base_url}/DrugPrdtPrmsnInfoService/getDrugPrdtPrmsnInq"
        params = {
            'serviceKey': self.api_key,
            'pageNo': page,
            'numOfRows': page_size,
            'type': 'json'
        }
        
        try:
            async with session.get(url, params=params) as response:
                data = await response.json()
                items = data.get('body', {}).get('items', [])
                return items if items else []
        except Exception as e:
            logger.error(f"페이지 {page} 수집 실패: {e}")
            return []
    
    def process_drug_data(self, raw_drugs: List[Dict]) -> pd.DataFrame:
        """약물 데이터 정제 및 구조화"""
        processed_drugs = []
        
        for drug in raw_drugs:
            processed = {
                'item_seq': drug.get('ITEM_SEQ', ''),
                'item_name': drug.get('ITEM_NAME', ''),
                'entp_name': drug.get('ENTP_NAME', ''),
                'main_ingredient': drug.get('MAIN_ITEM_INGR', ''),
                'atc_code': drug.get('ATC_CODE', ''),
                'storage_method': drug.get('STORAGE_METHOD', ''),
                'valid_term': drug.get('VALID_TERM', ''),
                'ee_doc': drug.get('EE_DOC_DATA', ''),  # 효능효과
                'ud_doc': drug.get('UD_DOC_DATA', ''),  # 용법용량
                'nb_doc': drug.get('NB_DOC_DATA', ''),  # 주의사항
            }
            processed_drugs.append(processed)
        
        return pd.DataFrame(processed_drugs)

# ===== 약물 상호작용 데이터베이스 구축 =====
class DrugInteractionDatabase:
    """약물 상호작용 데이터베이스"""
    
    def __init__(self):
        self.interactions = {}
        self.severity_levels = ['contraindicated', 'major', 'moderate', 'minor']
        
    def parse_drugbank_xml(self, xml_path: str):
        """DrugBank XML 파싱"""
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # XML 네임스페이스
        ns = {'db': 'http://www.drugbank.ca'}
        
        for drug in root.findall('db:drug', ns):
            drug_name = drug.find('db:name', ns).text
            drug_id = drug.find('db:drugbank-id[@primary="true"]', ns).text
            
            # 상호작용 파싱
            interactions = drug.find('db:drug-interactions', ns)
            if interactions is not None:
                for interaction in interactions.findall('db:drug-interaction', ns):
                    partner_id = interaction.find('db:drugbank-id', ns).text
                    description = interaction.find('db:description', ns).text
                    
                    # 한국어 약물명 매핑 필요
                    self._add_interaction(drug_name, partner_id, description)
    
    def _add_interaction(self, drug1: str, drug2: str, description: str):
        """상호작용 추가"""
        # 심각도 분류
        severity = self._classify_severity(description)
        
        key = tuple(sorted([drug1, drug2]))
        self.interactions[key] = {
            'drugs': list(key),
            'description': description,
            'severity': severity,
            'clinical_significance': self._extract_clinical_significance(description)
        }
    
    def _classify_severity(self, description: str) -> str:
        """상호작용 심각도 분류"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['fatal', 'life-threatening', 'contraindicated']):
            return 'contraindicated'
        elif any(word in description_lower for word in ['serious', 'major', 'significant']):
            return 'major'
        elif any(word in description_lower for word in ['moderate', 'caution']):
            return 'moderate'
        else:
            return 'minor'
    
    def _extract_clinical_significance(self, description: str) -> str:
        """임상적 중요도 추출"""
        # 키워드 기반 추출
        if 'bleeding' in description.lower():
            return '출혈 위험 증가'
        elif 'qtc' in description.lower() or 'arrhythmia' in description.lower():
            return '부정맥 위험'
        elif 'serotonin syndrome' in description.lower():
            return '세로토닌 증후군 위험'
        else:
            return '주의 관찰 필요'

# ===== 의료 지식 그래프 구축 =====
class MedicalKnowledgeGraph:
    """의료 지식 그래프"""
    
    def __init__(self):
        self.graph = {
            'diseases': {},
            'symptoms': {},
            'medications': {},
            'relations': []
        }
        
    def add_disease(self, icd_code: str, name_kr: str, name_en: str, 
                   symptoms: List[str], treatments: List[str]):
        """질병 정보 추가"""
        self.graph['diseases'][icd_code] = {
            'name_kr': name_kr,
            'name_en': name_en,
            'symptoms': symptoms,
            'treatments': treatments
        }
        
        # 관계 추가
        for symptom in symptoms:
            self.graph['relations'].append({
                'source': icd_code,
                'target': symptom,
                'type': 'has_symptom'
            })
        
        for treatment in treatments:
            self.graph['relations'].append({
                'source': icd_code,
                'target': treatment,
                'type': 'treated_by'
            })
    
    def find_related_diseases(self, symptom: str) -> List[str]:
        """증상과 관련된 질병 찾기"""
        related_diseases = []
        
        for relation in self.graph['relations']:
            if relation['target'] == symptom and relation['type'] == 'has_symptom':
                disease_code = relation['source']
                if disease_code in self.graph['diseases']:
                    related_diseases.append(self.graph['diseases'][disease_code]['name_kr'])
        
        return related_diseases
    
    def export_to_neo4j(self, uri: str, auth: tuple):
        """Neo4j로 그래프 내보내기"""
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(uri, auth=auth)
        
        with driver.session() as session:
            # 질병 노드 생성
            for icd_code, disease_info in self.graph['diseases'].items():
                session.run(
                    "CREATE (d:Disease {icd_code: $icd_code, name_kr: $name_kr, name_en: $name_en})",
                    icd_code=icd_code, 
                    name_kr=disease_info['name_kr'],
                    name_en=disease_info['name_en']
                )
            
            # 관계 생성
            for relation in self.graph['relations']:
                session.run(
                    "MATCH (a {id: $source}), (b {id: $target}) "
                    "CREATE (a)-[r:$type]->(b)",
                    source=relation['source'],
                    target=relation['target'],
                    type=relation['type']
                )

# ===== 데이터 품질 검증 =====
class DataQualityValidator:
    """데이터 품질 검증기"""
    
    def __init__(self):
        self.validation_rules = {
            'completeness': self._check_completeness,
            'consistency': self._check_consistency,
            'accuracy': self._check_accuracy
        }
        
    def validate_medical_record(self, record: Dict) -> Dict[str, float]:
        """의료 기록 검증"""
        scores = {}
        
        for rule_name, rule_func in self.validation_rules.items():
            scores[rule_name] = rule_func(record)
        
        scores['overall'] = np.mean(list(scores.values()))
        return scores
    
    def _check_completeness(self, record: Dict) -> float:
        """완전성 검사"""
        required_fields = ['patient_id', 'diagnosis', 'medications', 'date']
        present_fields = sum(1 for field in required_fields if record.get(field))
        
        return present_fields / len(required_fields)
    
    def _check_consistency(self, record: Dict) -> float:
        """일관성 검사"""
        score = 1.0
        
        # 날짜 형식 일관성
        if 'date' in record:
            try:
                datetime.strptime(record['date'], '%Y-%m-%d')
            except:
                score -= 0.2
        
        # ICD 코드 형식 검사
        if 'icd_code' in record:
            if not re.match(r'^[A-Z]\d{2}(\.\d{1,2})?$', record['icd_code']):
                score -= 0.2
        
        return max(0, score)
    
    def _check_accuracy(self, record: Dict) -> float:
        """정확성 검사 (규칙 기반)"""
        score = 1.0
        
        # 약물 용량 범위 검사
        if 'medications' in record:
            for med in record['medications']:
                if 'dosage' in med:
                    dosage = float(med['dosage'])
                    # 비정상적인 용량 검사
                    if dosage > 10000 or dosage < 0.001:
                        score -= 0.1
        
        return max(0, score)

# ===== 통합 데이터 파이프라인 실행 =====
async def run_data_pipeline():
    """전체 데이터 파이프라인 실행"""
    
    # 1. MIMIC-III 데이터 처리
    logger.info("MIMIC-III 데이터 처리 시작")
    mimic_processor = MIMICDataProcessor("./data/mimic-iii")
    notes_df = mimic_processor.load_mimic_notes()
    
    # 샘플링 (전체 데이터가 너무 크므로)
    sample_notes = notes_df.sample(n=1000, random_state=42)
    
    # 번역
    translated_texts = mimic_processor.translate_batch(
        sample_notes['TEXT'].tolist()
    )
    sample_notes['TEXT_KR'] = translated_texts
    
    # 2. 한국 의약품 데이터 수집
    logger.info("한국 의약품 데이터 수집 시작")
    drug_collector = KoreanDrugDataCollector(os.getenv('MFDS_API_KEY'))
    korean_drugs = await drug_collector.fetch_all_drugs()
    drugs_df = drug_collector.process_drug_data(korean_drugs)
    
    # 3. 약물 상호작용 DB 구축
    logger.info("약물 상호작용 데이터베이스 구축")
    interaction_db = DrugInteractionDatabase()
    interaction_db.parse_drugbank_xml('./data/drugbank.xml')
    
    # 4. 의료 지식 그래프 구축
    logger.info("의료 지식 그래프 구축")
    knowledge_graph = MedicalKnowledgeGraph()
    
    # ICD-10 코드와 질병 정보 매핑
    icd_mappings = {
        'E11': {'name_kr': '제2형 당뇨병', 'name_en': 'Type 2 diabetes mellitus',
                'symptoms': ['다뇨', '다음', '체중감소', '피로'],
                'treatments': ['메트포르민', '인슐린', '식이요법']},
        'I10': {'name_kr': '본태성 고혈압', 'name_en': 'Essential hypertension',
                'symptoms': ['두통', '어지러움', '흉통'],
                'treatments': ['암로디핀', 'ACE억제제', '베타차단제']}
    }
    
    for icd_code, info in icd_mappings.items():
        knowledge_graph.add_disease(
            icd_code=icd_code,
            name_kr=info['name_kr'],
            name_en=info['name_en'],
            symptoms=info['symptoms'],
            treatments=info['treatments']
        )
    
    # 5. 데이터 품질 검증
    logger.info("데이터 품질 검증")
    validator = DataQualityValidator()
    
    quality_scores = []
    for _, record in sample_notes.iterrows():
        record_dict = {
            'patient_id': record.get('SUBJECT_ID'),
            'diagnosis': record.get('TEXT_KR'),
            'date': record.get('CHARTDATE'),
            'medications': mimic_processor.extract_medications(record.get('TEXT', ''))
        }
        scores = validator.validate_medical_record(record_dict)
        quality_scores.append(scores)
    
    # 품질 보고서
    avg_scores = pd.DataFrame(quality_scores).mean()
    logger.info(f"평균 데이터 품질 점수:\n{avg_scores}")
    
    # 6. 데이터 저장
    logger.info("처리된 데이터 저장")
    
    # Parquet 형식으로 저장 (효율적인 저장 및 로드)
    sample_notes.to_parquet('./data/processed/mimic_notes_kr.parquet')
    drugs_df.to_parquet('./data/processed/korean_drugs.parquet')
    
    # 상호작용 DB 저장
    with open('./data/processed/drug_interactions.pkl', 'wb') as f:
        pickle.dump(interaction_db.interactions, f)
    
    # 지식 그래프 저장
    with open('./data/processed/medical_knowledge_graph.pkl', 'wb') as f:
        pickle.dump(knowledge_graph.graph, f)
    
    logger.info("데이터 파이프라인 완료")

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(run_data_pipeline())