from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Virtual Finance Advisor"

    # API Keys
    etoro_api_key: str = ""
    etoro_user_key: str = ""
    etoro_base_url: str = "https://api.etoro.com"
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
    bt_client_id: str = ""
    bt_client_secret: str = ""
    bt_base_url: str = "https://apistorebt.ro/bt/sb"
    bt_oauth_url: str = "https://apistorebt.ro/bt/sb/oauth2"
    
    # Load from .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"  # Ignore extra .env variables
    )

# Save in memory
@lru_cache()
def get_settings():
    return Settings()
