from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import os
import uuid
from pathlib import Path
import shutil
from datetime import datetime

# APIRouter 인스턴스 생성
router = APIRouter()

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 허용할 파일 확장자
ALLOWED_EXTENSIONS = {
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
    'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
    'medical': {'.dcm', '.nii', '.nifti'},  # 의료 이미지 파일
    'general': {'.zip', '.rar', '.7z'}
}

# 최대 파일 크기 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


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


@router.post("/upload", summary="단일 파일 업로드")
async def upload_file(
    file: UploadFile = File(..., description="업로드할 파일"),
    description: Optional[str] = Form(None, description="파일 설명")
):
    """
    단일 파일을 업로드합니다.
    
    - **file**: 업로드할 파일 (이미지, 문서, 의료 이미지 등)
    - **description**: 파일에 대한 설명 (선택사항)
    
    **지원 파일 형식:**
    - 이미지: jpg, jpeg, png, gif, bmp, webp
    - 문서: pdf, doc, docx, txt, rtf
    - 의료 이미지: dcm, nii, nifti
    - 압축파일: zip, rar, 7z
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
        
        return {
            "message": "파일 업로드 성공",
            "file_id": file_id,
            "original_filename": file.filename,
            "saved_filename": new_filename,
            "file_size": len(file_content),
            "file_category": category,
            "description": description,
            "upload_time": datetime.now().isoformat(),
            "file_url": f"/api/files/download/{file_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.post("/upload-multiple", summary="다중 파일 업로드")
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="업로드할 파일들"),
    description: Optional[str] = Form(None, description="파일들에 대한 공통 설명")
):
    """
    여러 개의 파일을 한 번에 업로드합니다.
    
    - **files**: 업로드할 파일 목록 (최대 5개)
    - **description**: 파일들에 대한 공통 설명 (선택사항)
    """
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="한 번에 최대 5개의 파일만 업로드 가능합니다.")
    
    upload_results = []
    failed_uploads = []
    
    for file in files:
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
            
            upload_results.append({
                "file_id": file_id,
                "original_filename": file.filename,
                "saved_filename": new_filename,
                "file_size": len(file_content),
                "file_category": category,
                "upload_time": datetime.now().isoformat(),
                "file_url": f"/api/files/download/{file_id}"
            })
            
        except Exception as e:
            failed_uploads.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "message": f"{len(upload_results)}개 파일 업로드 성공",
        "uploaded_files": upload_results,
        "failed_files": failed_uploads,
        "description": description,
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
                    return {
                        "file_id": file_id,
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "file_category": category_dir.name,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_extension": file_path.suffix,
                        "file_url": f"/api/files/download/{file_id}"
                    }
    
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
    
    - **category**: 파일 카테고리로 필터링 (images, documents, medical, general)
    """
    
    files_list = []
    
    search_dirs = [UPLOAD_DIR / category] if category else UPLOAD_DIR.iterdir()
    
    for category_dir in search_dirs:
        if category_dir.is_dir():
            for file_path in category_dir.iterdir():
                if file_path.is_file():
                    file_id = file_path.stem
                    stat = file_path.stat()
                    files_list.append({
                        "file_id": file_id,
                        "filename": file_path.name,
                        "file_size": stat.st_size,
                        "file_category": category_dir.name,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "file_url": f"/api/files/download/{file_id}"
                    })
    
    return {
        "total_files": len(files_list),
        "files": files_list,
        "filter_category": category
    }