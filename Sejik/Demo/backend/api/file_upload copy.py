# Sejik/Demo/backend/api/file_upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import os
import uuid
from pathlib import Path
import shutil
from datetime import datetime, timedelta

# 🆕 watsonx vision 및 캐시 imports
from utils.watsonx_vision import process_image_with_watsonx_vision_direct
from utils.cache import get_vision_result, set_vision_result, clear_vision_cache

# APIRouter 인스턴스 생성
router = APIRouter()

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 허용할 파일 확장자 (watsonx vision 처리 가능한 파일만)
ALLOWED_EXTENSIONS = {
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
    'documents': {'.pdf'}  # PDF는 나중에 지원 예정
}

# 최대 파일 크기 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Vision 재시도 제한
VISION_RETRY_LIMIT = 3  # 최대 3번까지 재시도
VISION_RETRY_COOLDOWN = 300  # 5분 쿨다운 (초)

# Vision 시도 기록 (메모리 기반 - 추후 DB로 이전)
vision_retry_tracker = {}


def get_file_category(filename: str) -> str:
    """파일 확장자를 기반으로 카테고리 분류"""
    ext = Path(filename).suffix.lower()

    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category
    return 'unknown'


def is_allowed_file(filename: str) -> bool:
    """허용된 파일 확장자인지 확인"""
    ext = Path(filename).suffix.lower()
    all_extensions = set()
    for extensions in ALLOWED_EXTENSIONS.values():
        all_extensions.update(extensions)
    return ext in all_extensions

# def analyze_with_watsonx_vision(file_path: Path, file_id: str):
#     """watsonx vision을 사용하여 의료 문서 분석"""
#     try:
#         # 텍스트 추출 전용 프롬프트
#         extraction_prompt = """이 이미지에서 모든 텍스트를 정확하게 추출해주세요.

# 특히 다음을 우선적으로 추출하세요:
# - 약물명, 성분명, 용법, 용량
# - 의료진 정보, 환자 정보
# - 날짜, 시간, 주의사항
# - 처방전 정보, 검사 결과
# - 기타 모든 텍스트

# 추출된 텍스트만 반환하고, 추가 설명이나 해석은 하지 마세요."""

#         # watsonx vision 호출 (file_path 직접 처리)
#         result = process_image_with_watsonx_vision_direct(file_path, extraction_prompt)

#         # 캐시에 저장 (file_id를 키로 사용)
#         vision_result = {
#             "success": True,
#             "text": result,
#             "processed_time": datetime.now().isoformat(),
#             "method": "watsonx_vision"
#         }

#         set_vision_result(file_id, vision_result)
#         return vision_result

#     except Exception as e:
#         error_result = {
#             "success": False,
#             "error": f"watsonx vision 처리 실패: {str(e)}",
#             "text": "",
#             "processed_time": datetime.now().isoformat(),
#             "method": "watsonx_vision"
#         }

#         # 실패한 경우도 캐시에 저장 (재시도 방지)
#         set_vision_result(file_id, error_result)
#         return error_result


@router.post("/upload", summary="단일 파일 업로드")
async def upload_file(
    file: UploadFile = File(..., description="업로드할 파일")
):
    """
    단일 파일을 업로드하고 watsonx vision 처리를 수행합니다.

    - **file**: 업로드할 파일 (watsonx vision 처리 가능한 파일만)

    **지원 파일 형식:**
    - 이미지: jpg, jpeg, png, gif, bmp, tiff, webp
    """

    # 파일 크기 확인
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 가능합니다."
        )

    # 파일 확장자 확인
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다."
        )

    try:
        # 고유한 파일명 생성
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        new_filename = f"{file_id}{file_extension}"

        # 카테고리별 디렉토리 생성
        category = get_file_category(file.filename)
        category_dir = UPLOAD_DIR / category
        category_dir.mkdir(exist_ok=True)

        # 파일 저장
        file_path = category_dir / new_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # 🆕 watsonx vision 처리
        try:
            vision_result = analyze_with_watsonx_vision(file_path, file_id)
        except Exception as vision_error:
            vision_result = {
                "success": False,
                "error": f"watsonx vision 처리 실패: {str(vision_error)}",
                "text": "",
                "method": "watsonx_vision"
            }
            set_vision_result(file_id, vision_result)

        response_data = {
            "message": "파일 업로드 성공",
            "file_id": file_id,
            "original_filename": file.filename,
            "saved_filename": new_filename,
            "file_size": len(file_content),
            "file_category": category,
            "upload_time": datetime.now().isoformat(),
            "file_url": f"/api/files/download/{file_id}"
        }

        # 🆕 watsonx vision 결과가 있으면 추가
        if vision_result:
            response_data["vision_result"] = vision_result

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.post("/upload-multiple", summary="다중 파일 업로드")
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="업로드할 파일들")
):
    """
    여러 개의 파일을 한 번에 업로드하고 watsonx vision 처리를 수행합니다.

    - **files**: 업로드할 파일들 (watsonx vision 처리 가능한 파일만, 최대 5개)

    **지원 파일 형식:**
    - 이미지: jpg, jpeg, png, gif, bmp, tiff, webp
    """

    if len(files) > 5:
        raise HTTPException(
            status_code=400, detail="한 번에 최대 5개의 파일만 업로드 가능합니다.")

    upload_results = []
    failed_uploads = []

    for i, file in enumerate(files):
        try:
            # 개별 파일 업로드 처리 (단일 업로드와 동일한 로직)
            file_content = await file.read()

            if len(file_content) > MAX_FILE_SIZE:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": f"파일 크기 초과 (최대 {MAX_FILE_SIZE // (1024*1024)}MB)"
                })
                continue

            if not is_allowed_file(file.filename):
                failed_uploads.append({
                    "filename": file.filename,
                    "error": "지원하지 않는 파일 형식"
                })
                continue

            # 파일 저장
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            new_filename = f"{file_id}{file_extension}"

            category = get_file_category(file.filename)
            category_dir = UPLOAD_DIR / category
            category_dir.mkdir(exist_ok=True)

            file_path = category_dir / new_filename
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)

            # 🆕 watsonx vision 처리
            try:
                vision_result = analyze_with_watsonx_vision(file_path, file_id)
            except Exception as vision_error:
                vision_result = {
                    "success": False,
                    "error": f"watsonx vision 처리 실패: {str(vision_error)}",
                    "text": ""
                }
                set_vision_result(file_id, vision_result)

            upload_result = {
                "file_id": file_id,
                "original_filename": file.filename,
                "saved_filename": new_filename,
                "file_size": len(file_content),
                "file_category": category,
                "upload_time": datetime.now().isoformat(),
                "file_url": f"/api/files/download/{file_id}"
            }

            if vision_result:
                upload_result["vision_result"] = vision_result

            upload_results.append(upload_result)

        except Exception as e:
            failed_uploads.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {
        "message": f"{len(upload_results)}개 파일 업로드 성공",
        "uploaded_files": upload_results,
        "failed_files": failed_uploads,
        "total_uploaded": len(upload_results),
        "total_failed": len(failed_uploads)
    }


@router.get("/download/{file_id}", summary="파일 다운로드")
async def download_file(file_id: str):
    """
    파일 ID를 사용하여 파일을 다운로드합니다.

    - **file_id**: 업로드 시 받은 파일 ID
    """

    # 모든 카테고리에서 파일 검색
    for category_dir in UPLOAD_DIR.iterdir():
        if category_dir.is_dir():
            for file_path in category_dir.glob(f"{file_id}.*"):
                if file_path.is_file():
                    return FileResponse(
                        path=file_path,
                        filename=file_path.name,
                        media_type='application/octet-stream'
                    )

    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")


@router.get("/info/{file_id}", summary="파일 정보 조회")
async def get_file_info(file_id: str):
    """
    파일 ID를 사용하여 파일 정보를 조회합니다.

    - **file_id**: 업로드 시 받은 파일 ID
    """

    for category_dir in UPLOAD_DIR.iterdir():
        if category_dir.is_dir():
            for file_path in category_dir.glob(f"{file_id}.*"):
                if file_path.is_file():
                    stat = file_path.stat()

                    # 캐시된 vision 결과도 함께 반환
                    vision_result = get_vision_result(file_id)

                    file_info = {
                        "file_id": file_id,
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "file_category": category_dir.name,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_extension": file_path.suffix,
                        "file_url": f"/api/files/download/{file_id}"
                    }

                    if vision_result:
                        file_info["vision_result"] = vision_result

                    return file_info

    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")


@router.delete("/delete/{file_id}", summary="파일 삭제")
async def delete_file(file_id: str):
    """
    파일 ID를 사용하여 파일을 삭제합니다.

    - **file_id**: 삭제할 파일의 ID
    """

    for category_dir in UPLOAD_DIR.iterdir():
        if category_dir.is_dir():
            for file_path in category_dir.glob(f"{file_id}.*"):
                if file_path.is_file():
                    file_path.unlink()

                    # 캐시에서도 제거
                    clear_vision_cache(file_id)

                    return {
                        "message": "파일 삭제 성공",
                        "file_id": file_id,
                        "deleted_file": file_path.name
                    }

    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")


@router.get("/list", summary="업로드된 파일 목록 조회")
async def list_files(category: Optional[str] = None):
    """
    업로드된 파일 목록을 조회합니다.

    - **category**: 파일 카테고리로 필터링 (images, documents)
    """

    files_list = []

    search_dirs = [UPLOAD_DIR / category] if category else UPLOAD_DIR.iterdir()

    for category_dir in search_dirs:
        if category_dir.is_dir():
            for file_path in category_dir.iterdir():
                if file_path.is_file():
                    file_id = file_path.stem
                    stat = file_path.stat()

                    file_info = {
                        "file_id": file_id,
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "file_category": category_dir.name,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "file_url": f"/api/files/download/{file_id}"
                    }

                    # 캐시된 vision 결과도 함께 표시
                    vision_result = get_vision_result(file_id)
                    if vision_result:
                        file_info["has_vision_result"] = vision_result.get(
                            "success", False)

                    files_list.append(file_info)

    return {
        "total_files": len(files_list),
        "files": files_list,
        "filter_category": category
    }


@router.post("/vision/{file_id}", summary="업로드된 파일 watsonx vision 재시도")
async def process_vision(file_id: str):
    """
    watsonx vision 처리 실패 파일에 대해 vision 처리를 재시도합니다.

    - **file_id**: vision 처리할 파일의 ID
    """

    # 파일 찾기
    file_path = None
    for category_dir in UPLOAD_DIR.iterdir():
        if category_dir.is_dir():
            for potential_file in category_dir.glob(f"{file_id}.*"):
                if potential_file.is_file():
                    file_path = potential_file
                    break
            if file_path:
                break

    if not file_path:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    # 지원하는 파일 형식 확인
    ext = file_path.suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp']:
        raise HTTPException(
            status_code=400,
            detail="watsonx vision을 지원하지 않는 파일 형식입니다. (지원: jpg, jpeg, png, bmp, tiff, gif, webp)"
        )

    # 재시도 제한 확인
    current_time = datetime.now()

    if file_id in vision_retry_tracker:
        retry_info = vision_retry_tracker[file_id]

        # 재시도 횟수 확인
        if retry_info['count'] >= VISION_RETRY_LIMIT:
            # 쿨다운 시간 확인
            time_since_last = (
                current_time - retry_info['last_attempt']).total_seconds()
            if time_since_last < VISION_RETRY_COOLDOWN:
                raise HTTPException(
                    status_code=429,
                    detail=f"watsonx vision 재시도 제한 초과. {VISION_RETRY_LIMIT}회 시도 완료. "
                    f"{int(VISION_RETRY_COOLDOWN - time_since_last)}초 후 다시 시도하세요."
                )
            else:
                # 쿨다운 후 리셋
                vision_retry_tracker[file_id] = {
                    'count': 0, 'last_attempt': current_time}
    else:
        # 첫 시도
        vision_retry_tracker[file_id] = {
            'count': 0, 'last_attempt': current_time}

    try:
        # 재시도 횟수 증가
        vision_retry_tracker[file_id]['count'] += 1
        vision_retry_tracker[file_id]['last_attempt'] = current_time

        # 기존 캐시 결과 제거
        clear_vision_cache(file_id)

        # watsonx vision 처리
        vision_result = analyze_with_watsonx_vision(file_path, file_id)

        # 성공 시 재시도 기록 삭제
        if file_id in vision_retry_tracker:
            del vision_retry_tracker[file_id]

        return {
            "file_id": file_id,
            "file_name": file_path.name,
            "file_category": file_path.parent.name,
            "vision_result": vision_result,
            "retry_info": {
                "attempt_number": vision_retry_tracker.get(file_id, {}).get('count', 0),
                "remaining_attempts": VISION_RETRY_LIMIT - vision_retry_tracker.get(file_id, {}).get('count', 0)
            }
        }

    except Exception as e:
        remaining_attempts = VISION_RETRY_LIMIT - \
            vision_retry_tracker[file_id]['count']

        if remaining_attempts > 0:
            raise HTTPException(
                status_code=500,
                detail=f"watsonx vision 처리 실패: {str(e)}. {remaining_attempts}번 더 시도 가능."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"watsonx vision 처리 최종 실패: {str(e)}. 모든 재시도 횟수를 소진했습니다. "
                f"{VISION_RETRY_COOLDOWN//60}분 후 다시 시도하세요."
            )
