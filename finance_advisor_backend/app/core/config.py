from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Virtual Finance Advisor"

    # API Keys
    etoro_api_key: str
    etoro_user_key: str
    etoro_base_url: str
    etoro_env: str = "demo"
    etoro_username: str

    alpha_vantage_api_key: str
    secret_key: str

    # Database
    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    # Load from .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"  # Ignore extra .env variables
    )

# Save in memory
@lru_cache()
def get_settings():
    return Settings()
