import json
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # Google Drive
    GOOGLE_SERVICE_ACCOUNT_FILE: str = ""
    DRIVE_INBOX_FOLDER_ID: str = ""
    DRIVE_SYNC_INTERVAL_MINUTES: int = 5
    DRIVE_DEFAULT_WORKSPACE_NAME: str = "Posteingang"

    @property
    def cors_origins_list(self) -> list[str]:
        return json.loads(self.CORS_ORIGINS)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
