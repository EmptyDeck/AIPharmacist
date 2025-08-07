#!/bin/bash

# 메모리 효율적인 Docker 빌드 스크립트
# EC2에서 다운되지 않도록 최적화된 설정

set -e  # 에러 시 스크립트 중단

echo "🚀 EC2 최적화된 Docker 빌드 시작..."

# Docker 시스템 정리 (메모리 확보)
echo "📦 Docker 시스템 정리 중..."
docker system prune -f --volumes 2>/dev/null || true

# Swap 메모리 상태 확인
echo "💾 메모리 상태 확인:"
free -h

# 빌드 전 빈 용량 확인
echo "💿 디스크 용량 확인:"
df -h /

# 메모리 제한과 함께 빌드 시작
echo "🔨 최적화된 빌드 시작..."

# BuildKit 비활성화 (레거시 빌더 사용으로 메모리 사용량 감소)
export DOCKER_BUILDKIT=0

# 병렬성 제한하여 메모리 압박 감소
docker build \
  --memory=3g \
  --memory-swap=4g \
  --cpu-quota=150000 \
  --cpu-period=100000 \
  --shm-size=512m \
  -t doctor_ai_backend \
  --progress=plain \
  . 2>&1 | tee build.log

# 빌드 성공 확인
if [ $? -eq 0 ]; then
    echo "✅ 빌드 성공!"
    
    # 이미지 크기 확인
    echo "📊 빌드된 이미지 정보:"
    docker images doctor_ai_backend
    
    # 사용하지 않는 빌드 캐시 정리
    echo "🧹 빌드 캐시 정리..."
    docker builder prune -f 2>/dev/null || true
    
    echo "🎉 모든 작업 완료!"
else
    echo "❌ 빌드 실패"
    echo "🔍 build.log 파일을 확인하세요"
    exit 1
fi