from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str 
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    SECRET_KEY:str 
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    class Config:
        env_file = ".env"
settings = Settings()
