from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    openai_api_key: str = "mock-key"
    openai_base_url: str = "http://localhost:18080/v1"
    github_token: Optional[str] = None
    hga_proxy_repo: Optional[str] = None

    # Load from .env file if present
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
