"""
데이터 처리 유틸리티
의료 챗봇을 위한 데이터 로딩, 검색, 처리 기능
"""

import pandas as pd
import streamlit as st
import requests
import json
import re
from typing import List, Dict, Optional, Tuple, Any
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """의료 데이터 처리 클래스"""
    
    def __init__(self):
        """DataProcessor 초기화"""
        self.drug_data = None
        self.sample_notes = None
        self._load_local_data()
    
    def _load_local_data(self):
        """로컬 데이터 파일들 로드"""
        try:
            # 약물 데이터 로드
            drug_file_path = Path("data/drug_data.csv")
            if drug_file_path.exists():
                self.drug_data = pd.read_csv(drug_file_path)
                logger.info(f"약물 데이터 로드 완료: {len(self.drug_data)}개 약물")
            else:
                logger.warning("drug_data.csv 파일을 찾을 수 없습니다.")
                self._create_default_drug_data()
            
            # 샘플 소견서 로드
            notes_file_path = Path("data/sample_notes.txt")
            if notes_file_path.exists():
                with open(notes_file_path, 'r', encoding='utf-8') as f:
                    self.sample_notes = f.read()
                logger.info("샘플 소견서 로드 완료")
            else:
                logger.warning("sample_notes.txt 파일을 찾을 수 없습니다.")
                
        except Exception as e:
            logger.error(f"로컬 데이터 로드 중 오류: {e}")
            self._create_default_drug_data()
    
    def _create_default_drug_data(self):
        """기본 약물 데이터 생성"""
        default_data = {
            '약품명': ['타이레놀정500mg', '낙센정', '부루펜시럽', '가스모틴정', '노르바스크정'],
            '제조회사': ['한국얀센', '동아제약', '삼일제약', '대웅제약', '화이자'],
            '주성분': ['아세트아미노펜', '나프록센', '이부프로펜', '모사프리드', '암로디핀'],
            '효능': ['해열진통', '소염진통', '해열진통', '소화촉진', '고혈압'],
            '용법용량': ['성인 1회 1-2정 1일 3-4회', '성인 1회 1정 1일 2회 식후복용', 
                      '소아 20-30mg/kg/일 3-4회 분복', '성인 1회 1정 1일 3회 식전복용', 
                      '성인 1일 1회 5-10mg'],
            '주의사항': ['간질환 환자 주의', '위궤양 환자 금기', '6개월 미만 금기', 
                      '간경화 환자 주의', '저혈압 환자 주의'],
            '상호작용': ['알코올과 병용 금지', '와파린과 상호작용', '아스피린과 병용 주의', 
                      '항콜린제와 상호작용', '자몽주스와 상호작용'],
            '부작용': ['위장장애 드물게 발생', '위장장애 복통', '위장장애 발진', 
                    '설사 복통', '부종 어지러움'],
            '보관방법': ['실온보관', '실온보관', '실온보관', '실온보관', '실온보관'],
            '가격': ['1500원', '2000원', '2500원', '1800원', '3000원']
        }
        self.drug_data = pd.DataFrame(default_data)
        logger.info("기본 약물 데이터 생성 완료")

    def search_drugs(self, query: str, limit: int = 5) -> List[Dict]:
        """
        약물 검색
        
        Args:
            query: 검색어
            limit: 반환할 최대 결과 수
            
        Returns:
            검색된 약물 정보 리스트
        """
        if self.drug_data is None:
            return []
        
        try:
            # 약품명, 주성분, 효능에서 검색
            mask = (
                self.drug_data['약품명'].str.contains(query, case=False, na=False) |
                self.drug_data['주성분'].str.contains(query, case=False, na=False) |
                self.drug_data['효능'].str.contains(query, case=False, na=False)
            )
            
            results = self.drug_data[mask].head(limit)
            
            # 딕셔너리 리스트로 변환
            drug_list = []
            for _, row in results.iterrows():
                drug_info = {
                    'name': row['약품명'],
                    'company': row['제조회사'],
                    'ingredient': row['주성분'],
                    'efficacy': row['효능'],
                    'usage': row['용법용량'],
                    'warnings': row['주의사항'],
                    'interactions': row['상호작용'],
                    'side_effects': row['부작용'],
                    'storage': row['보관방법'],
                    'price': row['가격']
                }
                drug_list.append(drug_info)
            
            logger.info(f"약물 검색 완료: '{query}' -> {len(drug_list)}개 결과")
            return drug_list
            
        except Exception as e:
            logger.error(f"약물 검색 중 오류: {e}")
            return []
    
    def check_drug_interactions(self, drugs: List[str], conditions: List[str] = None) -> List[str]:
        """
        약물 상호작용 체크
        
        Args:
            drugs: 약물 리스트
            conditions: 기저질환 리스트
            
        Returns:
            상호작용 경고 리스트
        """
        warnings = []
        
        # 위험한 약물 조합 정의
        dangerous_combinations = {
            '와파린': ['아스피린', '타이레놀', '이부프로펜', '낙센'],
            '디곡신': ['푸로세마이드', '스피로놀락톤'],
            '메트포르민': ['조영제', '알코올'],
            '리튬': ['이뇨제', 'ACE억제제'],
            '아스피린': ['와파린', '이부프로펜'],
            'MAO억제제': ['트라마돌', '세로토닌재흡수억제제']
        }
        
        # 약물-약물 상호작용 체크
        for i, drug1 in enumerate(drugs):
            for j, drug2 in enumerate(drugs):
                if i != j:
                    # 직접 매칭
                    if drug2 in dangerous_combinations.get(drug1, []):
                        warnings.append(f"⚠️ **{drug1}**과 **{drug2}** 동시 복용 시 상호작용 위험")
                    
                    # 부분 매칭 (약물명에 포함된 경우)
                    for dangerous_drug, interactions in dangerous_combinations.items():
                        if dangerous_drug in drug1.lower():
                            for interaction in interactions:
                                if interaction in drug2.lower():
                                    warnings.append(f"⚠️ **{drug1}**과 **{drug2}** 조합 주의 필요")
        
        # 기저질환-약물 상호작용 체크
        if conditions:
            condition_warnings = {
                '간질환': ['타이레놀', '아세트아미노펜'],
                '신장질환': ['메트포르민', '이부프로펜', '낙센'],
                '위궤양': ['아스피린', '이부프로펜', '낙센'],
                '심장질환': ['이부프로펜', '낙센'],
                '임신': ['와파린', '리튬', 'ACE억제제']
            }
            
            for condition in conditions:
                if condition in condition_warnings:
                    for drug in drugs:
                        for warning_drug in condition_warnings[condition]:
                            if warning_drug in drug:
                                warnings.append(f"⚠️ **{condition}** 환자는 **{drug}** 복용 시 주의 필요")
        
        return list(set(warnings))  # 중복 제거
    
    def process_medical_note(self, note: str) -> Dict[str, Any]:
        """
        의료 소견서 처리 및 정보 추출
        
        Args:
            note: 의료 소견서 텍스트
            
        Returns:
            추출된 정보 딕셔너리
        """
        try:
            # 기본 정보 추출을 위한 정규식 패턴들
            patterns = {
                'patient_info': r'환자[:\s]*([^,\n]+)',
                'age': r'(\d{1,3})세',
                'gender': r'(남|여)성?',
                'diagnosis': r'진단[:\s]*([^\n]+)',
                'prescription': r'처방[:\s]*([^\n]+)',
                'blood_pressure': r'혈압[:\s]*(\d+/\d+)',
                'temperature': r'체온[:\s]*(\d+\.?\d*)도?',
                'medications': r'(정|캡슐|시럽|mg|ml)',
            }
            
            extracted_info = {
                'raw_text': note,
                'patient_info': {},
                'vital_signs': {},
                'diagnosis': [],
                'medications': [],
                'warnings': []
            }
            
            # 환자 정보 추출
            age_match = re.search(patterns['age'], note)
            if age_match:
                extracted_info['patient_info']['age'] = int(age_match.group(1))
            
            gender_match = re.search(patterns['gender'], note)
            if gender_match:
                extracted_info['patient_info']['gender'] = gender_match.group(1)
            
            # 생체 징후 추출
            bp_match = re.search(patterns['blood_pressure'], note)
            if bp_match:
                extracted_info['vital_signs']['blood_pressure'] = bp_match.group(1)
            
            temp_match = re.search(patterns['temperature'], note)
            if temp_match:
                extracted_info['vital_signs']['temperature'] = float(temp_match.group(1))
            
            # 진단명 추출
            diagnosis_match = re.search(patterns['diagnosis'], note)
            if diagnosis_match:
                extracted_info['diagnosis'] = [diagnosis_match.group(1).strip()]
            
            # 약물명 추출 (간단한 패턴 매칭)
            drug_keywords = ['정', '캡슐', '시럽', 'mg', 'ml']
            lines = note.split('\n')
            for line in lines:
                if any(keyword in line for keyword in drug_keywords):
                    # 약물명 추출 로직 (간단화)
                    if '처방' in line or any(keyword in line for keyword in drug_keywords):
                        extracted_info['medications'].append(line.strip())
            
            logger.info(f"의료 소견서 처리 완료: {len(extracted_info['medications'])}개 약물 발견")
            return extracted_info
            
        except Exception as e:
            logger.error(f"의료 소견서 처리 중 오류: {e}")
            return {'error': str(e), 'raw_text': note}
    
    def get_drug_by_name(self, drug_name: str) -> Optional[Dict]:
        """
        약물명으로 상세 정보 조회
        
        Args:
            drug_name: 약물명
            
        Returns:
            약물 정보 딕셔너리 또는 None
        """
        if self.drug_data is None:
            return None
        
        try:
            # 정확한 매칭 시도
            exact_match = self.drug_data[self.drug_data['약품명'] == drug_name]
            if not exact_match.empty:
                row = exact_match.iloc[0]
                return {
                    'name': row['약품명'],
                    'company': row['제조회사'],
                    'ingredient': row['주성분'],
                    'efficacy': row['효능'],
                    'usage': row['용법용량'],
                    'warnings': row['주의사항'],
                    'interactions': row['상호작용'],
                    'side_effects': row['부작용'],
                    'storage': row['보관방법'],
                    'price': row['가격']
                }
            
            # 부분 매칭 시도
            partial_match = self.drug_data[
                self.drug_data['약품명'].str.contains(drug_name, case=False, na=False)
            ]
            if not partial_match.empty:
                row = partial_match.iloc[0]  # 첫 번째 결과 반환
                return {
                    'name': row['약품명'],
                    'company': row['제조회사'],
                    'ingredient': row['주성분'],
                    'efficacy': row['효능'],
                    'usage': row['용법용량'],
                    'warnings': row['주의사항'],
                    'interactions': row['상호작용'],
                    'side_effects': row['부작용'],
                    'storage': row['보관방법'],
                    'price': row['가격']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"약물 조회 중 오류: {e}")
            return None
    
    def get_sample_notes(self) -> List[str]:
        """
        샘플 의사 소견서 반환
        
        Returns:
            샘플 소견서 리스트
        """
        if not self.sample_notes:
            return [
                "환자는 45세 남성으로 고혈압 병력이 있습니다. 타이레놈 500mg 처방합니다.",
                "28세 여성 환자, 감기 증상으로 내원하여 해열진통제 처방하였습니다."
            ]
        
        # ## 으로 구분된 샘플들을 분리
        samples = self.sample_notes.split('## ')
        # 첫 번째 빈 요소 제거
        samples = [sample.strip() for sample in samples if sample.strip()]
        
        return samples[:8]  # 최대 8개 반환

# 편의 함수들
@st.cache_data
def load_drug_data() -> pd.DataFrame:
    """약물 데이터 로드 (캐시됨)"""
    processor = DataProcessor()
    return processor.drug_data

def search_drugs(query: str, limit: int = 5) -> List[Dict]:
    """약물 검색"""
    processor = DataProcessor()
    return processor.search_drugs(query, limit)

def check_drug_interactions(drugs: List[str], conditions: List[str] = None) -> List[str]:
    """약물 상호작용 체크"""
    processor = DataProcessor()
    return processor.check_drug_interactions(drugs, conditions)

def process_medical_note(note: str) -> Dict[str, Any]:
    """의료 소견서 처리"""
    processor = DataProcessor()
    return processor.process_medical_note(note)

def get_mfds_drug_info(drug_name: str) -> Dict:
    """
    식약처 API에서 약물 정보 조회
    
    Args:
        drug_name: 약물명
        
    Returns:
        약물 정보 딕셔너리
    """
    try:
        api_key = st.secrets.get("MFDS_API_KEY", "demo_key")
        url = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
        
        params = {
            'serviceKey': api_key,
            'itemName': drug_name,
            'numOfRows': 5,
            'pageNo': 1,
            'type': 'json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'body' in data and 'items' in data['body']:
                return data
        
        logger.warning(f"식약처 API 조회 실패: {drug_name}")
        return {}
        
    except Exception as e:
        logger.error(f"식약처 API 조회 중 오류: {e}")
        return {}

# 데이터 검증 함수들
def validate_drug_data(df: pd.DataFrame) -> bool:
    """약물 데이터 유효성 검증"""
    required_columns = ['약품명', '제조회사', '효능', '용법용량']
    return all(col in df.columns for col in required_columns)

def clean_drug_name(drug_name: str) -> str:
    """약물명 정제 (불필요한 문자 제거)"""
    # 기본적인 정제만 수행
    cleaned = re.sub(r'[^\w가-힣]', '', drug_name)
    return cleaned.strip()

def extract_dosage_info(usage_text: str) -> Dict[str, str]:
    """용법용량 텍스트에서 정보 추출"""
    dosage_info = {
        'frequency': '',
        'amount': '',
        'timing': ''
    }
    
    # 간단한 패턴 매칭
    if '1일' in usage_text:
        freq_match = re.search(r'1일\s*(\d+)회', usage_text)
        if freq_match:
            dosage_info['frequency'] = f"하루 {freq_match.group(1)}번"
    
    if '식후' in usage_text:
        dosage_info['timing'] = '식후 복용'
    elif '식전' in usage_text:
        dosage_info['timing'] = '식전 복용'
    elif '공복' in usage_text:
        dosage_info['timing'] = '공복시 복용'
    
    return dosage_info