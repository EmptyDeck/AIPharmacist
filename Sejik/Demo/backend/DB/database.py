from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    google_id = Column(String(100), unique=True, nullable=True)
    profile_picture = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # OAuth 토큰 정보
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ DB 테이블 생성 성공")
    except Exception as e:
        # 에러코드 보고싶으면 주석 해제
        # import logging, traceback
        # logging.error(f"❌ DB 테이블 생성 실패: {e}")
        # traceback.print_exc()
        # # pass 하면 그냥 진행 (서비스 중단 안됨)
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()