import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = str(Path(__file__).parent.parent.parent)

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
os.environ.setdefault(
    "HUGGINGFACE_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub")
)
os.environ.setdefault(
    "TRANSFORMERS_CACHE",
    str(Path.home() / ".cache" / "huggingface" / "transformers"),
)
os.environ.setdefault(
    "SENTENCE_TRANSFORMERS_HOME",
    str(Path.home() / ".cache" / "huggingface" / "sentence-transformers"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR, env_file_encoding="utf-8")

    # CometML config
    COMET_API_KEY: str | None = None
    COMET_WORKSPACE: str | None = None
    COMET_PROJECT: str = "llm-twin"

    # Embeddings config
    EMBEDDING_MODEL_ID: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_MODEL_MAX_INPUT_LENGTH: int = 512
    EMBEDDING_SIZE: int = 384
    EMBEDDING_MODEL_DEVICE: str = "cpu"

    # OpenAI
    OPENAI_MODEL_ID: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None

    # Groq
    GROQ_MODEL_ID: str = "llama-3.1-8b-instant"
    GROQ_API_KEY: str | None = None

    # MQ config
    RABBITMQ_DEFAULT_USERNAME: str = "guest"
    RABBITMQ_DEFAULT_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "mq"  # or localhost if running outside Docker
    RABBITMQ_PORT: int = 5672
    RABBITMQ_QUEUE_NAME: str = "default"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_STREAM_NAME: str = "mongo_events"

    # QdrantDB config
    QDRANT_DATABASE_HOST: str = "qdrant"  # or localhost if running outside Docker
    QDRANT_DATABASE_PORT: int = 6333
    USE_QDRANT_CLOUD: bool = (
        False  # if True, fill in QDRANT_CLOUD_URL and QDRANT_APIKEY
    )
    QDRANT_CLOUD_URL: str | None = None
    QDRANT_APIKEY: str | None = None


settings = Settings()
