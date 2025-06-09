import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings(BaseSettings):
    # API settings
    API_ENV: str = os.getenv("API_ENV", "development")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8001"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # PostgreSQL
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "Mauri3524")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "loanData")
    
     # MongoDB
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "loanData")
    
    # RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST", "/")
    
    # Colas de RabbitMQ
    USER_EVENTS_QUEUE: str = os.getenv("USER_EVENTS_QUEUE", "user_events")
    LOAN_EVENTS_QUEUE: str = os.getenv("LOAN_EVENTS_QUEUE", "loan_events")
    PAYMENT_EVENTS_QUEUE: str = os.getenv("PAYMENT_EVENTS_QUEUE", "payment_events")
    

    ENABLE_INITIAL_SYNC: bool = os.getenv("ENABLE_INITIAL_SYNC", "true").lower() == "true"
    # Database URL
    @property
    def postgres_url(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # MongoDB URL
    @property
    def mongo_connection_string(self):
        return self.MONGO_URI
    
    # RabbitMQ URL
    @property
    def rabbitmq_url(self):
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instancia de configuración global
settings = Settings()