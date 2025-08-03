# ===== API 서버 (FastAPI) =====
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uvicorn
import jwt
from datetime import datetime, timedelta
import hashlib
import redis
from sqlalchemy import create_engine, Column, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import asyncio
from contextlib import asynccontextmanager
import logging

# 데이터베이스 설정
DATABASE_URL = "postgresql://user:password@localhost/medical_chatbot"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis 설정 (캐싱)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# ===== 데이터 모델 =====
class ChatHistory(Base):
    """대화 기록 테이블"""
    __tablename__ = "chat_history"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)
    medical_document = Column(Text)
    conditions = Column(Text)  # JSON
    medications = Column(Text)  # JSON
    confidence_score = Column(Float)
    safety_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ===== Pydantic 모델 =====
class MedicalQuery(BaseModel):
    """의료 질의 요청 모델"""
    question: str = Field(..., description="사용자 질문")
    medical_document: Optional[str] = Field(None, description="의료 문서 (소견서, 처방전 등)")
    conditions: List[str] = Field(default_factory=list, description="기저질환 목록")
    medications: List[str] = Field(default_factory=list, description="복용 중인 약물 목록")
    session_id: Optional[str] = Field(None, description="세션 ID")

class MedicalResponse(BaseModel):
    """의료 응답 모델"""
    answer: str = Field(..., description="AI 응답")
    confidence_score: float = Field(..., description="응답 신뢰도 (0-1)")
    safety_warnings: List[str] = Field(default_factory=list, description="안전 경고")
    drug_interactions: List[Dict] = Field(default_factory=list, description="약물 상호작용")
    references: List[str] = Field(default_factory=list, description="참고 자료")
    session_id: str = Field(..., description="세션 ID")
    
class FeedbackRequest(BaseModel):
    """피드백 요청 모델"""
    session_id: str
    response_id: str
    rating: int = Field(..., ge=1, le=5, description="평점 (1-5)")
    comment: Optional[str] = None
    corrected_answer: Optional[str] = None

# ===== 보안 및 인증 =====
class SecurityManager:
    """보안 관리자"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.bearer = HTTPBearer()
        
    def create_token(self, user_id: str) -> str:
        """JWT 토큰 생성"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """토큰 검증"""
        token = credentials.credentials
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# ===== 개인정보 보호 =====
class PrivacyProtector:
    """개인정보 보호 클래스"""
    
    def __init__(self):
        self.sensitive_patterns = [
            (r'\d{6}-\d{7}', '[주민등록번호]'),
            (r'\d{3}-\d{3,4}-\d{4}', '[전화번호]'),
            (r'[가-힣]{2,4}\s*님', '[이름]'),
            (r'\d+세\s*[남여]성', '[나이/성별]')
        ]
    
    def anonymize_text(self, text: str) -> str:
        """민감 정보 익명화"""
        anonymized = text
        for pattern, replacement in self.sensitive_patterns:
            anonymized = re.sub(pattern, replacement, anonymized)
        return anonymized
    
    def hash_user_id(self, user_id: str) -> str:
        """사용자 ID 해싱"""
        return hashlib.sha256(user_id.encode()).hexdigest()

# ===== 캐싱 시스템 =====
class CacheManager:
    """캐시 관리자"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1시간
        
    def get_cached_response(self, query_hash: str) -> Optional[Dict]:
        """캐시된 응답 조회"""
        cached = self.redis.get(f"response:{query_hash}")
        if cached:
            return json.loads(cached)
        return None
    
    def cache_response(self, query_hash: str, response: Dict):
        """응답 캐싱"""
        self.redis.setex(
            f"response:{query_hash}",
            self.ttl,
            json.dumps(response, ensure_ascii=False)
        )
    
    def create_query_hash(self, query: MedicalQuery) -> str:
        """쿼리 해시 생성"""
        content = f"{query.question}:{','.join(query.conditions)}:{','.join(query.medications)}"
        return hashlib.md5(content.encode()).hexdigest()

# ===== 속도 제한 =====
class RateLimiter:
    """API 속도 제한"""
    
    def __init__(self, redis_client, max_requests: int = 100, window: int = 3600):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
        
    async def check_rate_limit(self, user_id: str) -> bool:
        """속도 제한 확인"""
        key = f"rate_limit:{user_id}"
        current = self.redis.incr(key)
        
        if current == 1:
            self.redis.expire(key, self.window)
        
        if current > self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per hour."
            )
        
        return True

# ===== 모델 서빙 =====
class ModelServer:
    """모델 서빙 클래스"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.rag_system = None
        self.drug_checker = None
        self.safety_validator = None
        
    async def load_models(self):
        """모델 비동기 로드"""
        logger.info("모델 로드 시작...")
        
        # 메인 모델 로드
        self.tokenizer = AutoTokenizer.from_pretrained("./models/medical-llm")
        self.model = AutoModelForCausalLM.from_pretrained(
            "./models/medical-llm",
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # RAG 시스템 초기화
        self.rag_system = MedicalRAGSystem()
        
        # 의료 지식 로드
        with open('./data/medical_knowledge.json', 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
        self.rag_system.build_index(knowledge)
        
        # 약물 상호작용 검사기
        self.drug_checker = DrugInteractionChecker()
        
        # 안전성 검증기
        self.safety_validator = MedicalSafetyValidator()
        
        logger.info("모델 로드 완료")
    
    async def generate_response(self, query: MedicalQuery) -> MedicalResponse:
        """응답 생성"""
        
        # RAG 검색
        relevant_docs = self.rag_system.retrieve(query.question, k=3)
        context = "\n".join([doc[0] for doc in relevant_docs])
        
        # 프롬프트 구성
        prompt = f"""당신은 의료 정보를 제공하는 AI 도우미입니다.

[관련 정보]
{context}

[환자 정보]
- 기저질환: {', '.join(query.conditions) if query.conditions else '없음'}
- 복용 약물: {', '.join(query.medications) if query.medications else '없음'}

[질문]
{query.question}

[답변] 반드시 다음 사항을 포함하세요:
1. 질문에 대한 명확한 답변
2. 주의사항이나 부작용
3. 의료진 상담이 필요한 경우 안내
"""
        
        # 토큰화
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        
        # 생성
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
        
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], 
            skip_special_tokens=True
        )
        
        # 약물 상호작용 검사
        interactions = []
        if query.medications:
            interactions = self.drug_checker.check_interactions(query.medications)
        
        # 안전성 검증
        safety_result = self.safety_validator.validate_response(generated_text)
        
        # 응답 구성
        response = MedicalResponse(
            answer=generated_text,
            confidence_score=self._calculate_confidence(relevant_docs),
            safety_warnings=safety_result['issues'],
            drug_interactions=interactions,
            references=[doc[0][:100] + "..." for doc in relevant_docs],
            session_id=query.session_id or self._generate_session_id()
        )
        
        return response
    
    def _calculate_confidence(self, relevant_docs: List[Tuple[str, float]]) -> float:
        """신뢰도 계산"""
        if not relevant_docs:
            return 0.5
        
        avg_distance = np.mean([doc[1] for doc in relevant_docs])
        confidence = max(0.3, min(0.95, 1 - (avg_distance / 100)))
        
        return round(confidence, 2)
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        return hashlib.md5(
            f"{datetime.utcnow().isoformat()}{os.urandom(16)}".encode()
        ).hexdigest()

# ===== FastAPI 앱 설정 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 시작 시 모델 로드
    await model_server.load_models()
    yield
    # 종료 시 정리
    logger.info("서버 종료")

app = FastAPI(
    title="의료 정보 챗봇 API",
    description="안전하고 정확한 의료 정보를 제공하는 AI 챗봇",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 객체 초기화
security_manager = SecurityManager(os.getenv("SECRET_KEY", "your-secret-key"))
privacy_protector = PrivacyProtector()
cache_manager = CacheManager(redis_client)
rate_limiter = RateLimiter(redis_client)
model_server = ModelServer()

# ===== API 엔드포인트 =====
@app.post("/api/v1/chat", response_model=MedicalResponse)
async def chat(
    query: MedicalQuery,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(security_manager.verify_token),
    db: Session = Depends(lambda: SessionLocal())
):
    """의료 질문에 대한 응답 생성"""
    
    # 속도 제한 확인
    await rate_limiter.check_rate_limit(user_id)
    
    # 개인정보 익명화
    query.question = privacy_protector.anonymize_text(query.question)
    if query.medical_document:
        query.medical_document = privacy_protector.anonymize_text(query.medical_document)
    
    # 캐시 확인
    query_hash = cache_manager.create_query_hash(query)
    cached_response = cache_manager.get_cached_response(query_hash)
    
    if cached_response:
        return MedicalResponse(**cached_response)
    
    # 응답 생성
    response = await model_server.generate_response(query)
    
    # 캐시 저장
    cache_manager.cache_response(query_hash, response.dict())
    
    # 백그라운드에서 대화 기록 저장
    background_tasks.add_task(
        save_chat_history,
        db, user_id, query, response
    )
    
    return response

@app.post("/api/v1/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    user_id: str = Depends(security_manager.verify_token)
):
    """사용자 피드백 제출"""
    
    # 피드백 저장 로직
    feedback_data = {
        'user_id': privacy_protector.hash_user_id(user_id),
        'session_id': feedback.session_id,
        'response_id': feedback.response_id,
        'rating': feedback.rating,
        'comment': feedback.comment,
        'corrected_answer': feedback.corrected_answer,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Redis에 피드백 저장 (나중에 배치 처리)
    redis_client.lpush('feedback_queue', json.dumps(feedback_data))
    
    return {"status": "success", "message": "피드백이 저장되었습니다."}

@app.get("/api/v1/drug/search")
async def search_drug(
    name: str,
    user_id: str = Depends(security_manager.verify_token)
):
    """약물 정보 검색"""
    
    # 약물 데이터베이스에서 검색
    # 실제 구현에서는 데이터베이스 쿼리
    drug_info = {
        'name': name,
        'generic_name': '...',
        'category': '...',
        'usage': '...',
        'side_effects': ['...'],
        'warnings': ['...']
    }
    
    return drug_info

@app.get("/api/v1/interactions/check")
async def check_interactions(
    medications: List[str],
    user_id: str = Depends(security_manager.verify_token)
):
    """약물 상호작용 확인"""
    
    interactions = model_server.drug_checker.check_interactions(medications)
    
    return {
        'medications': medications,
        'interactions': interactions,
        'checked_at': datetime.utcnow().isoformat()
    }

@app.get("/api/v1/health")
async def health_check():
    """헬스 체크"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'model_loaded': model_server.model is not None
    }

# ===== 헬퍼 함수 =====
def save_chat_history(db: Session, user_id: str, query: MedicalQuery, response: MedicalResponse):
    """대화 기록 저장"""
    chat_record = ChatHistory(
        id=response.session_id,
        user_id=privacy_protector.hash_user_id(user_id),
        session_id=response.session_id,
        question=query.question,
        answer=response.answer,
        medical_document=query.medical_document,
        conditions=json.dumps(query.conditions),
        medications=json.dumps(query.medications),
        confidence_score=response.confidence_score,
        safety_score=1.0 - len(response.safety_warnings) * 0.2
    )
    
    db.add(chat_record)
    db.commit()

# ===== 모니터링 및 로깅 =====
from prometheus_client import Counter, Histogram, generate_latest
import time

# 메트릭 정의
request_count = Counter('medical_chatbot_requests_total', 'Total requests')
request_duration = Histogram('medical_chatbot_request_duration_seconds', 'Request duration')
error_count = Counter('medical_chatbot_errors_total', 'Total errors')

@app.middleware("http")
async def add_metrics(request, call_next):
    """메트릭 수집 미들웨어"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        request_count.inc()
    except Exception as e:
        error_count.inc()
        raise e
    finally:
        request_duration.observe(time.time() - start_time)
    
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return generate_latest()

# ===== 메인 실행 =====
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )