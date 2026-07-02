from core import get_logger
from models.base import DataModel
from models.raw import ArticleRawModel, PostsRawModel, RepositoryRawModel

from data_logic.chunking_data_handlers import (
    ArticleChunkingHandler,
    ChunkingDataHandler,
    PostChunkingHandler,
    RepositoryChunkingHandler,
)
from data_logic.cleaning_data_handlers import (
    ArticleCleaningHandler,
    CleaningDataHandler,
    PostCleaningHandler,
    RepositoryCleaningHandler,
)
from data_logic.embedding_data_handlers import (
    ArticleEmbeddingHandler,
    EmbeddingDataHandler,
    PostEmbeddingHandler,
    RepositoryEmbeddingHandler,
)

logger = get_logger(__name__)


class RawDispatcher:
    @staticmethod
    def handle_mq_message(message: dict) -> DataModel | None:
        data_type = message.get("type")

        logger.info("Received message.", data_type=data_type)

        # Some crawlers/tests may send content as plain text; normalize for models.
        if isinstance(message.get("content"), str):
            message = {**message, "content": {"text": message["content"]}}

        try:
            if data_type == "posts":
                return PostsRawModel(**message)
            elif data_type == "articles":
                return ArticleRawModel(**message)
            elif data_type == "repositories":
                return RepositoryRawModel(**message)
        except Exception as exc:
            logger.error(
                "Dropping malformed message.",
                data_type=data_type,
                error=str(exc),
            )
            return None

        logger.warning("Unsupported data type received.", data_type=data_type)
        return None


class CleaningHandlerFactory:
    @staticmethod
    def create_handler(data_type) -> CleaningDataHandler:
        if data_type == "posts":
            return PostCleaningHandler()
        elif data_type == "articles":
            return ArticleCleaningHandler()
        elif data_type == "repositories":
            return RepositoryCleaningHandler()
        else:
            raise ValueError("Unsupported data type")


class CleaningDispatcher:
    cleaning_factory = CleaningHandlerFactory()

    @classmethod
    def dispatch_cleaner(cls, data_model: DataModel | None) -> DataModel | None:
        if data_model is None:
            return None

        data_type = data_model.type
        try:
            handler = cls.cleaning_factory.create_handler(data_type)
            clean_model = handler.clean(data_model)
            logger.info(
                "Data cleaned successfully.",
                data_type=data_type,
                cleaned_content_len=len(clean_model.cleaned_content),
            )
            return clean_model
        except Exception as exc:
            logger.error(
                "Failed to clean message.",
                data_type=data_type,
                error=str(exc),
            )
            return None


class ChunkingHandlerFactory:
    @staticmethod
    def create_handler(data_type) -> ChunkingDataHandler:
        if data_type == "posts":
            return PostChunkingHandler()
        elif data_type == "articles":
            return ArticleChunkingHandler()
        elif data_type == "repositories":
            return RepositoryChunkingHandler()
        else:
            raise ValueError("Unsupported data type")


class ChunkingDispatcher:
    cleaning_factory = ChunkingHandlerFactory

    @classmethod
    def dispatch_chunker(cls, data_model: DataModel) -> list[DataModel]:
        data_type = data_model.type
        handler = cls.cleaning_factory.create_handler(data_type)
        chunk_models = handler.chunk(data_model)

        logger.info(
            "Cleaned content chunked successfully.",
            num=len(chunk_models),
            data_type=data_type,
        )

        return chunk_models


class EmbeddingHandlerFactory:
    @staticmethod
    def create_handler(data_type) -> EmbeddingDataHandler:
        if data_type == "posts":
            return PostEmbeddingHandler()
        elif data_type == "articles":
            return ArticleEmbeddingHandler()
        elif data_type == "repositories":
            return RepositoryEmbeddingHandler()
        else:
            raise ValueError("Unsupported data type")


class EmbeddingDispatcher:
    cleaning_factory = EmbeddingHandlerFactory

    @classmethod
    def dispatch_embedder(cls, data_model: DataModel) -> DataModel:
        data_type = data_model.type
        handler = cls.cleaning_factory.create_handler(data_type)
        embedded_chunk_model = handler.embedd(data_model)

        logger.info(
            "Chunk embedded successfully.",
            data_type=data_type,
            embedding_len=len(embedded_chunk_model.embedded_content),
        )

        return embedded_chunk_model
