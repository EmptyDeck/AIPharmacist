from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 파일에서 변수를 읽어오도록 설정
    model_config = SettingsConfigDict(env_file=".env")

    # .env 파일에 정의한 변수들을 타입과 함께 선언
    # IBM Watson 설정
    WATSONX_API_URL: str = "https://us-south.ml.cloud.ibm.com"  # IBM Cloud URL
    WATSONX_API_KEY: str = ""  # IBM Cloud API Key
    WATSONX_PROJECT_ID: str = ""  # Watson Studio Project ID
    
    # 이메일 설정 (네이버 SMTP)
    MAIL_USERNAME: str = ""  # 네이버 이메일
    MAIL_PASSWORD: str = ""  # 네이버 앱 패스워드
    MAIL_FROM: str = ""      # 발신자 이메일
    
    # 팀원 모델 API 설정 (중계 서버용 - 백업)
    MODEL_API_URL: str = "http://localhost:5000"  # 팀원 모델 서버 주소
    MODEL_API_KEY: str = ""  # 팀원 모델 API 키 (필요시)
    
    # Naver OAuth 설정 (선택사항)
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""
    
    # Google OAuth 설정
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_PROJECT_ID: str = ""
    GOOGLE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URI: str = "https://oauth2.googleapis.com/token" 
    GOOGLE_AUTH_PROVIDER_X509_CERT_URL: str = "https://www.googleapis.com/oauth2/v1/certs"
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URIS: str = "http://3.34.3.40"
    
    # Database 설정
    DATABASE_URL: str = "mysql+pymysql://ibm.doctor-user:ibm.doctor-pass@localhost:3306/ibm.doctor-db"
    
    # MySQL 설정 (docker-compose에서 사용)
    MYSQL_ROOT_PASSWORD: str = ""
    MYSQL_DATABASE: str = ""
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""

# 설정 객체 생성
settings = Settings()