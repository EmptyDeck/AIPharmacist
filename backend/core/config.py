from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 파일에서 변수를 읽어오도록 설정
    model_config = SettingsConfigDict(env_file=".env")

    # .env 파일에 정의한 변수들을 타입과 함께 선언
    # 팀원 모델 API 설정
    MODEL_API_URL: str = ""  # 팀원 모델 서버 주소
    MODEL_API_KEY: str = ""  # 팀원 모델 API 키 (필요시)
    
    # Naver OAuth 설정
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    
    # 기존 WatsonX 설정 (백업용)
    WATSONX_API_URL: str = ""
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""

# 설정 객체 생성
settings = Settings()