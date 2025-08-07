# backend/utils/watsonx_vision.py
import base64
import requests
from pathlib import Path
from core.config import settings

def get_watson_token():
    """IBM Watson 토큰 발급"""
    try:
        token_response = requests.post(
            'https://iam.cloud.ibm.com/identity/token', 
            data={
                "apikey": settings.WATSONX_API_KEY, 
                "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'
            }
        )
        
        if token_response.status_code == 200:
            return token_response.json()["access_token"]
        else:
            raise Exception(f"토큰 발급 실패: {token_response.status_code}")
            
    except Exception as e:
        raise Exception(f"토큰 발급 에러: {str(e)}")

def get_mime_type(file_path: Path) -> str:
    """파일 확장자를 기반으로 MIME 타입 반환"""
    ext = file_path.suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.gif': 'image/gif',
        '.bmp': 'image/bmp', '.tiff': 'image/tiff',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')

def process_image_with_watsonx_vision(file_id: str, prompt: str = "이 이미지를 분석해주세요.") -> str:
    """
    파일 ID로 이미지를 찾아서 watsonx vision 모델로 처리
    
    Args:
        file_id (str): 업로드된 파일 ID
        prompt (str): 이미지 분석 명령어/질문
        
    Returns:
        str: watsonx vision 분석 결과
    """
    
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
        raise Exception("Vision 모델은 이미지 파일만 처리할 수 있습니다.")
    
    # 🆕 직접 처리 함수 호출
    return process_image_with_watsonx_vision_direct(file_path, prompt)

def process_image_with_watsonx_vision_direct(file_path: Path, prompt: str = "이 이미지를 분석해주세요.") -> str:
    """
    파일 경로로 직접 이미지를 처리 (file_id 검색 없이)
    
    Args:
        file_path (Path): 이미지 파일 경로
        prompt (str): 이미지 분석 명령어/질문
        
    Returns:
        str: watsonx vision 분석 결과
    """
    
    # 이미지 파일인지 확인
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    if file_path.suffix.lower() not in allowed_extensions:
        raise Exception("Vision 모델은 이미지 파일만 처리할 수 있습니다.")
    
    try:
        print(f"[INFO] watsonx Vision 직접 처리 시작: {file_path}")
        print(f"[INFO] 프롬프트: {prompt}")
        
        # 토큰 발급
        token = get_watson_token()
        
        # 이미지를 base64로 인코딩
        with open(file_path, "rb") as f:
            img_data = f.read()
            img64 = base64.b64encode(img_data).decode('utf-8')
        
        # MIME 타입 설정
        mime_type = get_mime_type(file_path)
        
        # watsonx vision 모델 호출
        headers = {
            'Content-Type': 'application/json', 
            'Authorization': f'Bearer {token}'
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        # watsonx AI 서비스 URL
        ai_service_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/c59e817c-448f-45f1-bc34-df12f190ac0d/ai_service?version=2021-05-01"
        
        response = requests.post(
            ai_service_url,
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 응답에서 텍스트 추출
            if 'choices' in result and len(result['choices']) > 0:
                answer = result['choices'][0]['message']['content'].strip()
                
                # 간단한 반복 제거 처리
                lines = answer.split('\n')
                unique_lines = []
                seen_lines = set()
                
                for line in lines:
                    line = line.strip()
                    if line and line not in seen_lines:
                        unique_lines.append(line)
                        seen_lines.add(line)
                
                cleaned_answer = '\n'.join(unique_lines)
                
                print(f"[INFO] watsonx Vision 직접 처리 완료: {len(cleaned_answer)} 글자")
                return cleaned_answer
                
            else:
                return "이미지를 분석할 수 없습니다."
        else:
            raise Exception(f"watsonx vision 호출 실패: {response.status_code}, {response.text}")
        
    except Exception as e:
        print(f"[ERROR] watsonx Vision 직접 처리 실패: {str(e)}")
        raise Exception(f"watsonx Vision 처리 실패: {str(e)}")
