# Database 관리

## 폴더 구조
```
DB/
├── README.md           # 이 파일
├── database.py         # SQLAlchemy 모델 및 연결 설정
├── init.sql           # 초기 데이터베이스 설정 스크립트
└── migrations/        # 향후 마이그레이션 파일들
```

## 파일 설명

### `database.py`
- SQLAlchemy 엔진 설정
- 데이터베이스 모델 정의 (User, ChatHistory 등)
- 데이터베이스 연결 함수 (`get_db()`)
- 테이블 생성 함수 (`create_tables()`)

### `init.sql`
- Docker Compose 실행 시 자동으로 실행되는 초기화 스크립트
- 데이터베이스, 사용자, 권한 설정
- 기본 테이블 생성 및 초기 데이터 삽입

## 데이터베이스 설정

### 현재 설정
- **데이터베이스**: `ibm.doctor-db`
- **사용자**: `ibm.doctor-user`
- **비밀번호**: `ibm.doctor-pass`
- **포트**: 3307 (외부 접근용)

### 연결 방법
```bash
# Docker 컨테이너 내부에서
mysql -u ibm.doctor-user -p ibm.doctor-db

# 외부에서 (호스트)
mysql -h localhost -P 3307 -u ibm.doctor-user -p ibm.doctor-db
```

## 개발 가이드

### 새 테이블 추가
1. `database.py`에 SQLAlchemy 모델 추가
2. 개발 환경에서 테스트
3. `init.sql`에 CREATE TABLE 문 추가 (선택사항)

### 데이터베이스 초기화
```bash
# 모든 데이터 삭제하고 재시작
docker-compose down -v
docker-compose up -d
```

### 백업 및 복원
```bash
# 백업
docker-compose exec mysql mysqldump -u root -p ibm.doctor-db > backup.sql

# 복원
docker-compose exec -T mysql mysql -u root -p ibm.doctor-db < backup.sql
```

## 주의사항
- 하이픈이 포함된 이름은 백틱(`)으로 감싸야 함
- 사용자 권한은 `%` (모든 호스트)로 설정
- 운영 환경에서는 더 강력한 비밀번호 사용 필요