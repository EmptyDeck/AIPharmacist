# backend/utils/cache.py
from datetime import datetime
from typing import Dict, Any

# 🆕 watsonx vision 결과 캐시 (메모리 기반)
vision_cache: Dict[str, Any] = {}

def get_vision_result(file_id: str) -> Dict[str, Any]:
    """캐시에서 vision 결과 조회"""
    return vision_cache.get(file_id)

def set_vision_result(file_id: str, result: Dict[str, Any]) -> None:
    """캐시에 vision 결과 저장"""
    result["cached_time"] = datetime.now().isoformat()
    vision_cache[file_id] = result

def clear_vision_cache(file_id: str = None) -> None:
    """캐시 정리"""
    if file_id:
        vision_cache.pop(file_id, None)
    else:
        vision_cache.clear()
