from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env 파일에서 변수를 읽어오도록 설정
    model_config = SettingsConfigDict(env_file=".env")

    # IBM Watson 설정
    WATSONX_API_URL: str = "https://us-south.ml.cloud.ibm.com"
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    
    # 이메일 설정
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    
    # 팀원 모델 API 설정
    MODEL_API_URL: str = "http://localhost:5000"
    MODEL_API_KEY: str = ""
    
    # Naver OAuth 설정
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    
    
    STT_API_KEY: str = ""
    STT_URL: str = ""
    TTS_API_KEY: str = ""
    TTS_URL: str = ""
    API_KEY: str = ""
    PROJECT_ID: str = ""
    IBM_CLOUD_URL: str = ""
    MODEL_ID: str = ""


# 설정 객체 생성
settings = Settings()
