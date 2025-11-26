from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MAX_PROMPT_TOKENS: int = 0
    MAX_HISTORY_TOKENS: int = 0
    TARGET_SUMMARY_TOKENS: int = 0

    class Config:
        env_file = ".env"

# 여기서 미리 생성해둡니다.
settings = Settings()