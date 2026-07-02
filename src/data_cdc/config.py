from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = str(Path(__file__).parent.parent.parent)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(ROOT_DIR) / ".env", env_file_encoding="utf-8"
    )

    MONGO_DATABASE_HOST: str = (
        "mongodb://mongo1:30001,mongo2:30002,mongo3:30003/?replicaSet=my-replica-set"
    )
    MONGO_DATABASE_NAME: str = "twin"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_STREAM_NAME: str = "mongo_events"

settings = Settings()
