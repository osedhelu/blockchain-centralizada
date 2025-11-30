import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "blockchain_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "blockchain_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "blockchain_pass")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "redis_pass")
    
    # RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "rabbitmq_user")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "rabbitmq_pass")
    
    # Blockchain
    BLOCKCHAIN_DIFFICULTY: int = int(os.getenv("BLOCKCHAIN_DIFFICULTY", "4"))
    BLOCKCHAIN_MINING_REWARD: float = float(os.getenv("BLOCKCHAIN_MINING_REWARD", "100"))
    
    # API
    BLOCKCHAIN_API_PORT: int = int(os.getenv("BLOCKCHAIN_API_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/%2F"


settings = Settings()

