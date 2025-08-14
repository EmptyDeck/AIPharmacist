# backend/utils/watsonx_vision.py
import os
import io
from PIL import Image
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
    allowed_extensions = {'.jpg', '.jpeg',
                          '.png', '.gif', '.bmp', '.tiff', '.webp'}
    if file_path.suffix.lower() not in allowed_extensions:
        raise Exception("Vision 모델은 이미지 파일만 처리할 수 있습니다.")

    # 🆕 직접 처리 함수 호출
    return process_image_with_watsonx_vision_direct(file_path, prompt)


# def process_image_with_watsonx_vision_direct(file_path: Path, prompt: str = "이 이미지를 분석해주세요.") -> str:
#     """
#     파일 경로로 직접 이미지를 처리 (file_id 검색 없이)

#     Args:
#         file_path (Path): 이미지 파일 경로
#         prompt (str): 이미지 분석 명령어/질문

#     Returns:
#         str: watsonx vision 분석 결과
#     """
#     print("process_image_with_watsonx_vision_direct")
#     # 이미지 파일인지 확인
#     allowed_extensions = {'.jpg', '.jpeg',
#                           '.png', '.gif', '.bmp', '.tiff', '.webp'}
#     if file_path.suffix.lower() not in allowed_extensions:
#         raise Exception("Vision 모델은 이미지 파일만 처리할 수 있습니다.")

#     try:
#         print(f"[INFO] watsonx Vision 직접 처리 시작: {file_path}")
#         print(f"[INFO] 프롬프트: {prompt}")

#         # 토큰 발급
#         token = get_watson_token()

#         # 이미지를 base64로 인코딩
#         with open(file_path, "rb") as f:
#             img_data = f.read()
#             img64 = base64.b64encode(img_data).decode('utf-8')

#         # MIME 타입 설정
#         mime_type = get_mime_type(file_path)

#         # watsonx vision 모델 호출
#         headers = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {token}'
#         }

#         payload = {
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": prompt},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:{mime_type};base64,{img64}"
#                             }
#                         }
#                     ]
#                 }
#             ],
#             "max_tokens": 1500,
#             "temperature": 0.7
#         }

#         # watsonx AI 서비스 URL
#         ai_service_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/c59e817c-448f-45f1-bc34-df12f190ac0d/ai_service?version=2021-05-01"

#         response = requests.post(
#             ai_service_url,
#             json=payload,
#             headers=headers
#         )

#         if response.status_code == 200:
#             result = response.json()

#             # 응답에서 텍스트 추출
#             if 'choices' in result and len(result['choices']) > 0:
#                 answer = result['choices'][0]['message']['content'].strip()

#                 # 간단한 반복 제거 처리
#                 lines = answer.split('\n')
#                 unique_lines = []
#                 seen_lines = set()

#                 for line in lines:
#                     line = line.strip()
#                     if line and line not in seen_lines:
#                         unique_lines.append(line)
#                         seen_lines.add(line)

#                 cleaned_answer = '\n'.join(unique_lines)

#                 print(
#                     f"[INFO] watsonx Vision 직접 처리 완료: {len(cleaned_answer)} 글자")
#                 return cleaned_answer

#             else:
#                 return "이미지를 분석할 수 없습니다."
#         else:
#             raise Exception(
#                 f"watsonx vision 호출 실패: {response.status_code}, {response.text}")

#     except Exception as e:
#         print(f"[ERROR] watsonx Vision 직접 처리 실패: {str(e)}")
#         raise Exception(f"watsonx Vision 처리 실패: {str(e)}")

# def process_image_with_watsonx_vision_direct(file_path: Path, prompt: str = "이 이미지를 분석해주세요.") -> str:
#     """
#     파일 경로로 직접 이미지를 처리 (file_id 검색 없이)

#     Args:
#         file_path (Path): 이미지 파일 경로
#         prompt (str): 이미지 분석 명령어/질문

#     Returns:
#         str: watsonx vision 분석 결과
#     """
#     print("process_image_with_watsonx_vision_direct")

#     # 이미지 파일인지 확인
#     allowed_extensions = {'.jpg', '.jpeg',
#                           '.png', '.gif', '.bmp', '.tiff', '.webp'}
#     if file_path.suffix.lower() not in allowed_extensions:
#         raise Exception("Vision 모델은 이미지 파일만 처리할 수 있습니다.")

#     try:
#         print(f"[INFO] watsonx Vision 직접 처리 시작: {file_path}")
#         print(f"[INFO] 프롬프트: {prompt}")

#         # 토큰 발급
#         token = get_watson_token()

#         # 이미지를 base64로 인코딩
#         with open(file_path, "rb") as f:
#             img_data = f.read()
#             img64 = base64.b64encode(img_data).decode('utf-8')

#         # MIME 타입 설정
#         mime_type = get_mime_type(file_path)

#         # watsonx vision 모델 호출
#         headers = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {token}'
#         }

#         # 🔥 반복 방지를 위한 개선된 페이로드
#         payload = {
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": prompt},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:{mime_type};base64,{img64}"
#                             }
#                         }
#                     ]
#                 }
#             ],
#             # 🔧 반복 방지 파라미터 추가
#             "max_tokens": 100,           # 토큰 수 대폭 줄임 (1500 → 150)
#             "temperature": 0.3,          # 온도 낮춤 (0.7 → 0.3)
#             "top_p": 0.9,               # 확률 분포 제한
#             "frequency_penalty": 2,    # 빈도 페널티 추가
#             "presence_penalty": 0.6,     # 존재 페널티 추가
#             "repetition_penalty": 1.5,   # 반복 페널티 추가
#             "stop": ["이상입니다"],  # 중단 토큰 추가
#             "seed": 42                   # 시드 고정으로 일관성 유지

#         }

#         # watsonx AI 서비스 URL
#         ai_service_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/c59e817c-448f-45f1-bc34-df12f190ac0d/ai_service?version=2021-05-01"

#         response = requests.post(
#             ai_service_url,
#             json=payload,
#             headers=headers
#         )

#         if response.status_code == 200:
#             result = response.json()

#             # 응답에서 텍스트 추출
#             if 'choices' in result and len(result['choices']) > 0:
#                 answer = result['choices'][0]['message']['content'].strip()

#                 # 🔥 간단한 반복 제거 처리 (기존 로직 유지)
#                 lines = answer.split('\n')
#                 unique_lines = []
#                 seen_lines = set()

#                 for line in lines:
#                     line = line.strip()
#                     if line and line not in seen_lines:
#                         unique_lines.append(line)
#                         seen_lines.add(line)

#                 cleaned_answer = '\n'.join(unique_lines)

#                 print(
#                     f"[INFO] watsonx Vision 직접 처리 완료: {len(cleaned_answer)} 글자")
#                 return cleaned_answer

#             else:
#                 return "이미지를 분석할 수 없습니다."
#         else:
#             raise Exception(
#                 f"watsonx vision 호출 실패: {response.status_code}, {response.text}")

#     except Exception as e:
#         print(f"[ERROR] watsonx Vision 직접 처리 실패: {str(e)}")
#         raise Exception(f"watsonx Vision 처리 실패: {str(e)}")


def process_image_with_watsonx_vision_direct(file_path: Path, prompt: str = "이 이미지를 분석해주세요.") -> str:
    """
    LLM 업로드 안전 전처리 + watsonx Vision 호출
    - RGB 변환 + sRGB 색공간 표준화
    - EXIF/ICC/XMP 등 메타데이터 제거
    - 항상 JPEG 변환 (표준 4:2:0)
    - 1920px 이하 리사이즈
    - 500KB 이하 압축
    """

    print("process_image_with_watsonx_vision_direct")

    allowed_extensions = {'.jpg', '.jpeg',
                          '.png', '.gif', '.bmp', '.tiff', '.webp'}
    if file_path.suffix.lower() not in allowed_extensions:
        raise Exception("Vision 모델은 이미지 파일만 처리할 수 있습니다.")

    try:
        print(f"[INFO] watsonx Vision 직접 처리 시작: {file_path}")
        print(f"[INFO] 프롬프트: {prompt}")

        # ===== 이미지 로드 & RGB 변환 =====
        img = Image.open(file_path).convert("RGB")

        # ===== 1920px 이하로 리사이즈 =====
        max_dim = 1920
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim))

        # ===== 메타데이터 제거 + JPEG 변환 + 압축 =====
        buffer = io.BytesIO()
        quality = 90
        while True:
            buffer.seek(0)
            img.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,  # progressive JPEG로 호환성 강화
                subsampling=2      # 4:2:0 표준 서브샘플링
            )
            size_kb = buffer.tell() / 1024
            if size_kb <= 500 or quality <= 20:
                break
            quality -= 5

        print(f"[INFO] 최종 이미지 크기: {size_kb:.1f}KB, 품질: {quality}")

        # ===== base64 인코딩 =====
        img64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = "image/jpeg"

        # ===== Watsonx Vision API 호출 =====
        token = get_watson_token()
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
            "max_tokens": 100,
            "temperature": 0.3,
            "top_p": 0.9,
            "frequency_penalty": 2,
            "presence_penalty": 0.6,
            "repetition_penalty": 1.5,
            "stop": ["이상입니다"],
            "seed": 42
        }

        ai_service_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/c59e817c-448f-45f1-bc34-df12f190ac0d/ai_service?version=2021-05-01"
        response = requests.post(ai_service_url, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                answer = result['choices'][0]['message']['content'].strip()
                # 중복 줄 제거
                lines = answer.split('\n')
                unique_lines, seen = [], set()
                for line in lines:
                    line = line.strip()
                    if line and line not in seen:
                        unique_lines.append(line)
                        seen.add(line)
                return '\n'.join(unique_lines)
            else:
                return "이미지를 분석할 수 없습니다."
        else:
            raise Exception(
                f"watsonx vision 호출 실패: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"[ERROR] watsonx Vision 직접 처리 실패: {str(e)}")
        raise Exception(f"watsonx Vision 처리 실패: {str(e)}")
