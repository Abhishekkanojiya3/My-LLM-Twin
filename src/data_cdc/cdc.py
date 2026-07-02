import json
import logging

from bson import json_util
from config import settings
from core.db.mongo import MongoDatabaseConnector
from core.logger_utils import get_logger
# from core.mq import publish_to_rabbitmq
from core.mq import publish_to_redis

logger = get_logger(__file__)


def stream_process():
    try:
        client = MongoDatabaseConnector()
        db = client["twin"]
        logging.info("Connected to MongoDB.")

        # Watch all DB changes and filter to inserts in Python.
        changes = db.watch()
        for change in changes:
            if change.get("operationType") != "insert":
                continue

            data_type = change["ns"]["coll"]
            entry_id = str(change["fullDocument"]["_id"])  # Convert ObjectId to string

            change["fullDocument"].pop("_id", None)
            change["fullDocument"]["type"] = data_type
            change["fullDocument"]["entry_id"] = entry_id

            if data_type not in ["articles", "posts", "repositories"]:
                logging.info(f"Unsupported data type: '{data_type}'")
                continue

            try:
                # Use json_util to serialize the document
                data = json.dumps(change["fullDocument"], default=json_util.default)
                logger.info(
                    f"Change detected and serialized for a data sample of type {data_type}."
                )

                publish_to_redis(stream_name=settings.REDIS_STREAM_NAME, data=data)
                logger.info(f"Data '{data_type}' Redis Stream mein publish ho gaya.")
            except Exception as e:
                logger.error(f"Failed to process change for '{data_type}': {e}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    stream_process()
