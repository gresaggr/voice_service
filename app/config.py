from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Получаем путь к корню проекта (на уровень выше от app/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Bot Configuration
    bot_token: str = Field(..., description="Telegram Bot Token")
    webhook_host: str = Field(default="", description="Webhook host")
    webhook_path: str = Field(default="/webhook", description="Webhook path")
    webapp_host: str = Field(default="0.0.0.0", description="Webapp host")
    webapp_port: int = Field(default=8000, description="Webapp port")

    # Database Configuration
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(..., description="Database name")
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")

    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database")

    # RabbitMQ Configuration
    rabbitmq_host: str = Field(default="localhost", description="RabbitMQ host")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_user: str = Field(default="guest", description="RabbitMQ user")
    rabbitmq_password: str = Field(default="guest", description="RabbitMQ password")

    # Payment Configuration
    yoomoney_token: str = Field(default="", description="YooMoney token")
    telegram_stars_token: str = Field(default="", description="Telegram Stars token")

    # Service Configuration
    service_cost: float = Field(default=10.0, description="Service cost per use")
    free_usage_hours: int = Field(default=24, description="Hours between free uses")
    max_voice_duration: int = Field(default=300, description="Max voice message duration")

    # Environment
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Debug mode")

    # Security
    secret_key: str = Field(..., description="Secret key for encryption")
    jwt_secret: str = Field(..., description="JWT secret key")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"


settings = Settings()
