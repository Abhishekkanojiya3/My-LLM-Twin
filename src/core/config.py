import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = str(Path(__file__).parent.parent.parent)

os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(Path.home() / ".cache" / "huggingface" / "transformers"))
os.environ.setdefault(
    "SENTENCE_TRANSFORMERS_HOME",
    str(Path.home() / ".cache" / "huggingface" / "sentence-transformers"),
)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(ROOT_DIR) / ".env", env_file_encoding="utf-8")

    # MongoDB configs
    MONGO_DATABASE_HOST: str = (
        "mongodb://mongo1:30001,mongo2:30002,mongo3:30003/?replicaSet=my-replica-set"
    )
    MONGO_DATABASE_NAME: str = "twin"

    # MQ config
    RABBITMQ_DEFAULT_USERNAME: str = "guest"
    RABBITMQ_DEFAULT_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "mq"
    RABBITMQ_PORT: int = 5673

    # QdrantDB config
    QDRANT_CLOUD_URL: str = "str"
    QDRANT_DATABASE_HOST: str = "qdrant"
    QDRANT_DATABASE_PORT: int = 6333
    USE_QDRANT_CLOUD: bool = False
    QDRANT_APIKEY: str | None = None

    # OpenAI config
    OPENAI_MODEL_ID: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None

    # Groq config
    GROQ_MODEL_ID: str = "llama-3.1-8b-instant"
    GROQ_API_KEY: str | None = None

    # CometML config
    COMET_API_KEY: str | None = None
    COMET_WORKSPACE: str | None = None
    COMET_PROJECT: str = "llm-twin"

    # AWS Authentication
    AWS_REGION: str = "eu-central-1"
    AWS_ACCESS_KEY: str | None = None
    AWS_SECRET_KEY: str | None = None
    AWS_ARN_ROLE: str | None = None

    # LLM Model config
    HUGGINGFACE_ACCESS_TOKEN: str | None = None
    MODEL_ID: str = "unsloth/Meta-Llama-3.1-8B-Instruct"
    DEPLOYMENT_ENDPOINT_NAME: str = "twin"

    MAX_INPUT_TOKENS: int = 1536  # Max length of input text.
    MAX_TOTAL_TOKENS: int = 2048  # Max length of the generation (including input text).
    MAX_BATCH_TOTAL_TOKENS: int = 2048  # Limits the number of tokens that can be processed in parallel during the generation.

    # Embeddings config
    EMBEDDING_MODEL_ID: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_MODEL_MAX_INPUT_LENGTH: int = 512
    EMBEDDING_SIZE: int = 384
    EMBEDDING_MODEL_DEVICE: str = "cpu"

    def patch_localhost(self) -> None:
        self.MONGO_DATABASE_HOST = "mongodb://localhost:30001,localhost:30002,localhost:30003/?replicaSet=my-replica-set"
        self.QDRANT_DATABASE_HOST = "localhost"
        self.RABBITMQ_HOST = "localhost"


settings = AppSettings()
