from pydantic import BaseSetting

class Settings(BaseSetting):
    LLM_MODE: str = "llmam3"
    APP_NAME: str = "LangChain Agent"
    APP_VERSION: str = "1.0.0"
    
    # DB 설정 (MariaDB)
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

class Config:
    env_file= ".env"

settings = Settings()