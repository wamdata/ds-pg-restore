from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings, str_strip_whitespace=True):
    model_config = SettingsConfigDict(
        env_file=".env", secrets_dir="/run/secrets", env_nested_delimiter="_"
    )

    S3_BUCKET_NAME: str
    S3_KEY: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    DOWNLOAD_FILE: Path
    PRE_PROCESSING_SQL: Path | None = None
    POST_PROCESSING_SQL: Path | None = None

    # Database connection
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str


settings = Settings()