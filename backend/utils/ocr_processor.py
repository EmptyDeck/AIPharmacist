import os
import sys
import pytesseract
from PIL import Image
import PyPDF2
from pathlib import Path
from typing import Union, Dict, Any

class OCRProcessor:
    """의료 문서 OCR 처리를 위한 클래스"""
    
    def __init__(self):
        self._setup_tesseract()
    
    def _setup_tesseract(self):
        """운영체제에 따라 Tesseract 경로 설정"""
        # 환경변수에 있으면 자동으로 찾음
        # 없으면 기본 경로 시도
        if sys.platform.startswith('win'):
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
    def extract_text(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        파일에서 텍스트 추출 (이미지 + PDF 지원)
        
        Args:
            file_path (Union[str, Path]): 파일 경로
        
        Returns:
            Dict[str, Any]: 추출 결과
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"파일을 찾을 수 없습니다: {file_path}",
                "text": ""
            }
        
        ext = file_path.suffix.lower()
        
        try:
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
                return self._extract_from_image(file_path)
            elif ext == '.pdf':
                return self._extract_from_pdf(file_path)
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 파일 형식: {ext}",
                    "text": ""
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"처리 중 오류 발생: {str(e)}",
                "text": ""
            }
    
    def _extract_from_image(self, image_path: Path) -> Dict[str, Any]:
        """이미지에서 텍스트 추출 (한국어 + 영어)"""
        try:
            image = Image.open(image_path)
            
            # 한국어 + 영어로 OCR
            text_kor_eng = pytesseract.image_to_string(image, lang='kor+eng')
            
            # 한국어만
            text_kor = pytesseract.image_to_string(image, lang='kor')
            
            # 영어만
            text_eng = pytesseract.image_to_string(image, lang='eng')
            
            # 텍스트 정리
            cleaned_text = self._clean_text(text_kor_eng)
            
            return {
                "success": True,
                "error": None,
                "text": cleaned_text,
                "text_variants": {
                    "korean_english": text_kor_eng,
                    "korean_only": text_kor,
                    "english_only": text_eng
                },
                "file_type": "image",
                "file_name": image_path.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"이미지 처리 오류: {str(e)}",
                "text": ""
            }
    
    def _extract_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """PDF에서 텍스트 추출"""
        try:
            text = ""
            pages_info = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            cleaned_page_text = self._clean_text(page_text)
                            text += f"--- 페이지 {page_num} ---\n{cleaned_page_text}\n\n"
                            pages_info.append({
                                "page": page_num,
                                "text": cleaned_page_text,
                                "success": True
                            })
                        else:
                            pages_info.append({
                                "page": page_num,
                                "text": "",
                                "success": False,
                                "error": "텍스트 없음"
                            })
                    except Exception as e:
                        pages_info.append({
                            "page": page_num,
                            "text": "",
                            "success": False,
                            "error": str(e)
                        })
            
            return {
                "success": True,
                "error": None,
                "text": text.strip(),
                "file_type": "pdf",
                "file_name": pdf_path.name,
                "total_pages": len(pdf_reader.pages),
                "pages_info": pages_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF 처리 오류: {str(e)}",
                "text": ""
            }
    
    def _clean_text(self, text: str) -> str:
        """추출된 텍스트 정리"""
        if not text:
            return ""
        
        # 줄별로 분리하고 공백 제거
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 정리된 텍스트 반환
        return '\n'.join(lines)
    
    def analyze_medical_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        의료 문서 특화 분석
        
        Args:
            file_path (Union[str, Path]): 파일 경로
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        result = self.extract_text(file_path)
        
        if not result["success"]:
            return result
        
        text = result["text"]
        
        # 의료 문서 키워드 검색
        medical_keywords = {
            "진단서": ["진단서", "의료진단서", "diagnosis"],
            "처방전": ["처방전", "prescription", "처방"],
            "검사결과": ["검사결과", "test result", "혈액검사", "소변검사", "엑스레이"],
            "병원": ["병원", "의원", "클리닉", "hospital", "clinic"],
            "의사": ["의사", "doctor", "주치의"],
            "환자": ["환자", "patient", "성명", "이름"],
            "증상": ["증상", "symptom", "통증", "아픔"],
            "약물": ["약물", "medicine", "medication", "약", "투약"]
        }
        
        detected_keywords = {}
        for category, keywords in medical_keywords.items():
            found_keywords = [kw for kw in keywords if kw.lower() in text.lower()]
            if found_keywords:
                detected_keywords[category] = found_keywords
        
        # 결과에 의료 문서 분석 정보 추가
        result["medical_analysis"] = {
            "detected_keywords": detected_keywords,
            "document_type": self._classify_medical_document(detected_keywords),
            "confidence": self._calculate_confidence(detected_keywords)
        }
        
        return result
    
    def _classify_medical_document(self, detected_keywords: Dict) -> str:
        """감지된 키워드를 바탕으로 문서 유형 분류"""
        if "진단서" in detected_keywords:
            return "diagnosis_certificate"
        elif "처방전" in detected_keywords:
            return "prescription"
        elif "검사결과" in detected_keywords:
            return "test_result"
        elif any(key in detected_keywords for key in ["병원", "의사", "환자"]):
            return "medical_document"
        else:
            return "unknown"
    
    def _calculate_confidence(self, detected_keywords: Dict) -> float:
        """키워드 감지를 바탕으로 신뢰도 계산"""
        if not detected_keywords:
            return 0.0
        
        total_categories = len(detected_keywords)
        max_categories = 8  # 전체 의료 키워드 카테고리 수
        
        return min(total_categories / max_categories, 1.0)


# 편의 함수들
def extract_text_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """파일에서 텍스트 추출하는 편의 함수"""
    processor = OCRProcessor()
    return processor.extract_text(file_path)


def analyze_medical_document(file_path: Union[str, Path]) -> Dict[str, Any]:
    """의료 문서 분석하는 편의 함수"""
    processor = OCRProcessor()
    return processor.analyze_medical_document(file_path)


# 사용 예시
if __name__ == "__main__":
    # 테스트용 코드
    processor = OCRProcessor()
    
    # 테스트 파일 경로
    test_file = "test_image.jpg"
    
    if os.path.exists(test_file):
        print(f"처리 중: {test_file}")
        print("=" * 50)
        
        result = processor.analyze_medical_document(test_file)
        
        if result["success"]:
            print("✅ 텍스트 추출 성공")
            print(f"📄 추출된 텍스트:\n{result['text']}")
            print(f"🏥 의료 문서 분석: {result['medical_analysis']}")
        else:
            print(f"❌ 오류: {result['error']}")
    else:
        print(f"❌ 테스트 파일을 찾을 수 없습니다: {test_file}")