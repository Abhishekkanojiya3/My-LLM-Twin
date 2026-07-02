
import json
from typing import Self
import redis
from config import settings
from core.logger_utils import get_logger

logger = get_logger(__file__)


class RedisConnection:
    """
    Singleton class — poore system mein ek hi
    Redis connection instance rahega.
    
    RabbitMQ mein 'pika.BlockingConnection' tha,
    yahan 'redis.Redis' hai — lekin idea same hai.
    """

    _instance = None

    def __new__(cls, *args, **kwargs) -> Self:
        # Agar instance exist nahi karta, tabhi naya banao
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        password: str | None = None,
        fail_silently: bool = False,
    ) -> None:
        self.host = host or settings.REDIS_HOST
        self.port = port or settings.REDIS_PORT
        self.password = password or settings.REDIS_PASSWORD
        self.fail_silently = fail_silently
        self._client = None

    def connect(self):
        """Redis se connection banao."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                decode_responses=True,  # bytes ki jagah string milega
            )
            # Test karo ki connection actually kaam kar raha hai
            self._client.ping()
            logger.info("Redis se connection successful.")
        except redis.exceptions.ConnectionError as e:
            logger.exception("Redis se connect nahi hua.")
            if not self.fail_silently:
                raise e

    def is_connected(self) -> bool:
        """Check karo ki connection open hai ya nahi."""
        try:
            return self._client is not None and self._client.ping()
        except Exception:
            return False

    def get_client(self) -> redis.Redis:
        """Redis client return karo — isse xadd/xread call karenge."""
        if not self.is_connected():
            self.connect()
        return self._client

    def close(self):
        """Connection band karo."""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis connection close ho gaya.")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def publish_to_redis(stream_name: str, data: str):
    """
    Redis Stream mein data publish karo.
    
    RabbitMQ mein tha:
        channel.basic_publish(exchange="", routing_key=queue_name, body=data)
    
    Redis mein hai:
        client.xadd(stream_name, {"data": data})
    
    xadd kya karta hai?
    - Stream mein ek naya entry add karta hai
    - Har entry ko ek unique ID milta hai (timestamp-based)
    - Message history log mein rehti hai — delete nahi hoti
    """
    try:
        conn = RedisConnection()
        client = conn.get_client()

        # xadd = "stream add"
        # stream_name = RabbitMQ mein queue_name tha
        # {"data": data} = message payload
        # maxlen = stream kitna bada ho sakta hai (memory control)
        message_id = client.xadd(
            stream_name,
            {"data": data},
            maxlen=10000,   # zyada purane messages auto-delete ho jaayenge
            approximate=True
        )

        logger.info(
            f"Redis Stream '{stream_name}' mein publish hua. "
            f"Message ID: {message_id}"
        )

    except redis.exceptions.RedisError as e:
        logger.exception(f"Redis mein publish karne mein error: {e}")
        raise


# ---- Consumer side bhi likhte hain (Feature Pipeline ke liye) ----

def consume_from_redis(
    stream_name: str,
    group_name: str,
    consumer_name: str,
    count: int = 10,
):
    """
    Redis Stream se messages consume karo.
    
    RabbitMQ mein tha:
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
    
    Redis mein Consumer Groups use karte hain:
    - Group = ek logical subscriber (jaise 'feature-pipeline')
    - Consumer = group ke andar ek worker (jaise 'worker-1')
    - Isse multiple workers same stream se alag messages le sakte hain
    """
    try:
        conn = RedisConnection()
        client = conn.get_client()

        # Group exist nahi karta toh banao
        try:
            client.xgroup_create(
                stream_name,
                group_name,
                id="0",          # "0" = shuruat se padho
                mkstream=True    # stream bhi banao agar exist nahi karti
            )
            logger.info(f"Consumer group '{group_name}' bana.")
        except redis.exceptions.ResponseError:
            # Group pehle se exist karta hai — koi baat nahi
            pass

        # Messages padho
        # ">" ka matlab = sirf naye unread messages do
        messages = client.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={stream_name: ">"},
            count=count,
            block=5000,   # 5 seconds wait karo agar koi message nahi
        )

        return messages

    except redis.exceptions.RedisError as e:
        logger.exception(f"Redis se consume karne mein error: {e}")
        raise


def acknowledge_message(stream_name: str, group_name: str, message_id: str):
    """
    Message process ho gaya — RabbitMQ mein ye 'ack' tha.
    Redis mein 'xack' hai.
    
    Ye important hai — agar ack nahi kiya toh Redis
    sochega ki message process nahi hua aur dobara bhejega.
    """
    conn = RedisConnection()
    client = conn.get_client()
    client.xack(stream_name, group_name, message_id)