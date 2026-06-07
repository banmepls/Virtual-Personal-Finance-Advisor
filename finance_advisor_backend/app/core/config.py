from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Virtual Finance Advisor"

    # API Keys
    etoro_api_key: str = ""
    etoro_user_key: str = ""
    etoro_base_url: str = "https://public-api.etoro.com"
    etoro_env: str = "demo"
    etoro_username: str = "demo_user"

    alpha_vantage_api_key: str = ""
    secret_key: str = "default_secret_key_for_dev_only"
    google_api_key: str = ""

    use_mock_data: bool = True

    # Database
    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str

    # Banca Transilvania Open Banking (PSD2)
    use_bt_sandbox: bool = True
    bt_client_id: str = "sandbox_client_id"
    bt_client_secret: str = "sandbox_client_secret"
    bt_base_url: str = "https://api.apistorebt.ro/bt/sb"
    bt_redirect_uri: str = "http://localhost:8001/api/v1/bank/oauth2/callback"
    bt_frontend_redirect_uri: str = "http://localhost:3000/dashboard"
    
    # Load from .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"  # Ignore extra .env variables
    )

# Save in memory
@lru_cache()
def get_settings():
    return Settings()
