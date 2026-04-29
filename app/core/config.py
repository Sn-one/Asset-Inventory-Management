from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Asset Inventory Management API"
    app_version: str = "0.2.0"
    database_url: str = Field(default="sqlite:///./asset_inventory.db")
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
