-- 초기 데이터베이스 설정
CREATE DATABASE IF NOT EXISTS doctor_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 권한 설정 (이미 docker-compose에서 생성되지만 추가 권한을 위해)
GRANT ALL PRIVILEGES ON doctor_ai.* TO 'doctoruser'@'%';
FLUSH PRIVILEGES;