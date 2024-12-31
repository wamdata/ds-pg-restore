from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings, str_strip_whitespace=True):
    model_config = SettingsConfigDict(
        env_file=".env",
        secrets_dir="/run/secrets" if Path("/run/secrets").exists() else None,
    )

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_KEY: str
    DOWNLOAD_FILE: Path = Path("./data/dl/s3_file.sql.gz")
    PRE_PROCESSING_SQL: Path | None = None
    POST_PROCESSING_SQL: Path | None = None

    # Database connection
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str


settings = Settings()
