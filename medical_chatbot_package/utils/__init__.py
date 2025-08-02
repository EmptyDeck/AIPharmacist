"""
Utils 패키지 초기화 파일
의료 챗봇 프로젝트의 유틸리티 함수들을 포함합니다.
"""

# 버전 정보
__version__ = "1.0.0"
__author__ = "Medical Chatbot Team"

# 주요 모듈 import
from .watsonx_client import WatsonxClient
from .data_processor import DataProcessor

# 편의를 위한 alias
from .watsonx_client import (
    setup_watsonx_client,
    generate_response,
    analyze_medical_text
)

from .data_processor import (
    load_drug_data,
    search_drugs,
    check_drug_interactions,
    process_medical_note
)

# 패키지에서 공개할 항목들
__all__ = [
    'WatsonxClient',
    'DataProcessor',
    'setup_watsonx_client',
    'generate_response', 
    'analyze_medical_text',
    'load_drug_data',
    'search_drugs',
    'check_drug_interactions',
    'process_medical_note'
]