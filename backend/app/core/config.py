from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://siteguard:siteguard_secret@localhost:5432/siteguard"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change_me_in_production"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Scanner
    SCANNER_MAX_PAGES: int = 10
    SCANNER_TIMEOUT: int = 15

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
