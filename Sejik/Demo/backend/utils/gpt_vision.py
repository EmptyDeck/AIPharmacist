# backend/utils/gpt_vision.py
import base64
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from core.config import settings


# Gemini 설정
if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("[WARNING] GEMINI_API_KEY가 설정되지 않았습니다.")


def get_mime_type(file_path: Path) -> str:
    """파일 확장자를 기반으로 MIME 타입 반환"""
    ext = file_path.suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', 
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def process_single_image_with_gemini(file_path: Path, user_question: str = "") -> Dict[str, Any]:
    """단일 이미지를 Gemini Vision으로 분석"""
    
    try:
        # Gemini Vision 모델 사용
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # 이미지 파일을 base64로 인코딩
        with open(file_path, "rb") as f:
            img_data = f.read()
            img64 = base64.b64encode(img_data).decode('utf-8')
        
        # MIME 타입 설정
        mime_type = get_mime_type(file_path)
        
        # 의료 문서 텍스트 추출 전용 프롬프트
        extraction_prompt = """이 이미지에서 모든 텍스트를 정확하게 추출해주세요.

특히 다음을 우선적으로 추출하세요:
- 약물명/성분명
- 용법/용량 정보  
- 주의사항
- 처방 정보
- 의료진 정보
- 날짜/시간 정보
- 기타 모든 텍스트

추출된 텍스트만 반환하고, 설명이나 해석은 하지 마세요."""

        # generate_content 호출
        resp = model.generate_content(
            contents=[
                {"text": extraction_prompt},
                {"inline_data": {"mime_type": mime_type, "data": img64}}
            ]
        )
        
        extracted_text = resp.text.strip() if resp.text else ""
        
        return {
            "success": True,
            "extracted_text": extracted_text,
            "file_path": str(file_path),
            "mime_type": mime_type,
            "error": None
        }
        
    except Exception as e:
        print(f"[ERROR] Gemini Vision 처리 실패: {str(e)}")
        return {
            "success": False,
            "extracted_text": "",
            "file_path": str(file_path),
            "mime_type": None,
            "error": str(e)
        }


def process_multiple_images_with_gemini(file_paths: List[Path], user_question: str = "") -> Dict[str, Any]:
    """여러 이미지를 Gemini Vision으로 분석"""
    
    results = []
    all_extracted_text = []
    errors = []
    
    for file_path in file_paths:
        result = process_single_image_with_gemini(file_path, user_question)
        results.append(result)
        
        if result["success"]:
            all_extracted_text.append(result["extracted_text"])
        else:
            errors.append(f"{file_path.name}: {result['error']}")
    
    # 모든 텍스트를 합치기
    combined_text = "\n\n=== 다음 이미지 ===\n\n".join(all_extracted_text)
    
    return {
        "success": len(all_extracted_text) > 0,
        "combined_text": combined_text,
        "individual_results": results,
        "total_images": len(file_paths),
        "successful_extractions": len(all_extracted_text),
        "errors": errors
    }


def process_image_with_gemini_vision(file_id: str, user_question: str = "") -> str:
    """파일 ID로 이미지를 찾아서 Gemini Vision으로 텍스트 추출"""
    
    # 업로드된 파일 찾기
    upload_dir = Path("uploads")
    file_path = None
    
    for category_dir in upload_dir.iterdir():
        if category_dir.is_dir():
            for potential_file in category_dir.glob(f"{file_id}.*"):
                if potential_file.is_file():
                    file_path = potential_file
                    break
        if file_path:
            break
    
    if not file_path:
        raise Exception("업로드된 파일을 찾을 수 없습니다.")
    
    # 이미지 파일인지 확인
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    if file_path.suffix.lower() not in allowed_extensions:
        raise Exception("Gemini Vision은 이미지 파일만 처리할 수 있습니다.")
    
    print(f"[INFO] Gemini Vision 처리 시작: {file_path}")
    
    # 단일 이미지 처리
    result = process_single_image_with_gemini(file_path, user_question)
    
    if result["success"]:
        extracted_text = result["extracted_text"]
        
        if not extracted_text.strip():
            return "이미지에서 텍스트를 추출할 수 없었습니다. 이미지가 명확하지 않거나 텍스트가 없는 이미지일 수 있습니다."
        
        print(f"[INFO] Gemini Vision 텍스트 추출 성공: {len(extracted_text)} 글자")
        return extracted_text
        
    else:
        raise Exception(f"Gemini Vision 처리 실패: {result['error']}")


# 🆕 여러 파일 ID 지원 함수 (추후 확장용)
def process_multiple_images_with_gemini_vision(file_ids: List[str], user_question: str = "") -> str:
    """여러 파일 ID로 이미지들을 찾아서 Gemini Vision으로 텍스트 추출"""
    
    file_paths = []
    upload_dir = Path("uploads")
    
    # 모든 파일 경로 찾기
    for file_id in file_ids:
        file_path = None
        for category_dir in upload_dir.iterdir():
            if category_dir.is_dir():
                for potential_file in category_dir.glob(f"{file_id}.*"):
                    if potential_file.is_file():
                        file_path = potential_file
                        break
            if file_path:
                break
        
        if file_path:
            file_paths.append(file_path)
        else:
            print(f"[WARNING] 파일을 찾을 수 없음: {file_id}")
    
    if not file_paths:
        raise Exception("처리할 이미지 파일을 찾을 수 없습니다.")
    
    # 여러 이미지 처리
    result = process_multiple_images_with_gemini(file_paths, user_question)
    
    if result["success"]:
        return result["combined_text"]
    else:
        error_msg = "; ".join(result["errors"])
        raise Exception(f"Gemini Vision 처리 실패: {error_msg}")
def process_image_with_gemini_conversation(file_id: str, user_question: str = "") -> str:
    """파일 ID로 이미지를 찾아서 Gemini Vision으로 직접 대화"""
    
    # 업로드된 파일 찾기 (기존 로직과 동일)
    upload_dir = Path("uploads")
    file_path = None
    
    for category_dir in upload_dir.iterdir():
        if category_dir.is_dir():
            for potential_file in category_dir.glob(f"{file_id}.*"):
                if potential_file.is_file():
                    file_path = potential_file
                    break
        if file_path:
            break
    
    if not file_path:
        raise Exception("업로드된 파일을 찾을 수 없습니다.")
    
    # 이미지 파일인지 확인
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    if file_path.suffix.lower() not in allowed_extensions:
        raise Exception("Gemini Vision은 이미지 파일만 처리할 수 있습니다.")
    
    try:
        print(f"[INFO] Gemini Vision 대화 처리 시작: {file_path}")
        
        # Gemini Vision 모델 사용
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # 이미지 파일을 base64로 인코딩
        with open(file_path, "rb") as f:
            img_data = f.read()
            img64 = base64.b64encode(img_data).decode('utf-8')
        
        # MIME 타입 설정
        mime_type = get_mime_type(file_path)
        
        # 의료 AI 어시스턴트 프롬프트
        conversation_prompt = f"""당신은 의료 전문 AI 어시스턴트 Dr. Watson입니다{user_question}"""

        # generate_content 호출
        resp = model.generate_content(
            contents=[
                {"text": conversation_prompt},
                {"inline_data": {"mime_type": mime_type, "data": img64}}
            ]
        )
        
        result = resp.text.strip() if resp.text else "이미지를 분석할 수 없습니다."
        
        print(f"[INFO] Gemini Vision 대화 완료: {len(result)} 글자")
        return result
        
    except Exception as e:
        print(f"[ERROR] Gemini Vision 대화 처리 실패: {str(e)}")
        raise Exception(f"Gemini Vision 대화 실패: {str(e)}")
