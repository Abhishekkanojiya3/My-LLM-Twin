import json
import time
from datetime import datetime
from typing import Generic, Iterable, List, Optional, TypeVar

from bytewax.inputs import FixedPartitionedSource, StatefulSourcePartition
from config import settings
from core import get_logger
from core.mq import RedisConnection  # RabbitMQConnection ki jagah

logger = get_logger(__name__)

DataT = TypeVar("DataT")
MessageT = TypeVar("MessageT")


class RedisStreamPartition(StatefulSourcePartition, Generic[DataT, MessageT]):
    """
    Bytewax aur Redis Stream ke beech connection banata hai.
    
    RabbitMQ mein tha:
        channel.basic_get(queue=queue_name)  — ek message lo
    
    Redis mein hai:
        client.xreadgroup(...) — consumer group se messages lo
    
    Consumer Group kyun?
        Agar multiple Bytewax workers hain, toh har worker
        alag message lega — duplicate processing nahi hogi.
    """

    def __init__(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        resume_state: MessageT | None = None,
    ) -> None:
        self._in_flight_msg_ids = resume_state or set()
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name

        # Redis connection banao
        self.connection = RedisConnection()
        self.connection.connect()
        self.client = self.connection.get_client()

        # Consumer group banao agar exist nahi karta
        self._ensure_consumer_group()

    def _ensure_consumer_group(self):
        """
        Consumer group banao.
        RabbitMQ mein queue automatically exist karti thi —
        Redis mein group manually banana padta hai.
        """
        try:
            self.client.xgroup_create(
                self.stream_name,
                self.group_name,
                id="$",        # sirf naye messages lo
                mkstream=True  # stream bhi banao agar nahi hai
            )
            logger.info(
                f"Consumer group '{self.group_name}' bana.",
                stream=self.stream_name
            )
        except Exception:
            # Group pehle se exist karta hai — bilkul theek hai
            pass

    def next_batch(self, sched: Optional[datetime]) -> Iterable[DataT]:
        """
        Redis Stream se ek batch messages lo.
        
        RabbitMQ mein tha:
            method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        
        Redis mein hai:
            messages = client.xreadgroup(groupname, consumername, streams, count)
        """
        try:
            # ">" = sirf naye unread messages do
            messages = self.client.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.stream_name: ">"},
                count=10,     # ek baar mein max 10 messages
                block=1000,   # 1 second wait karo agar koi message nahi
            )
        except Exception:
            logger.error(
                f"Redis Stream se message fetch karne mein error.",
                stream_name=self.stream_name,
            )
            time.sleep(10)  # 10 second baad retry

            # Reconnect karo
            self.connection.connect()
            self.client = self.connection.get_client()
            return []

        if not messages:
            return []

        result = []
        # messages format: [(stream_name, [(msg_id, {data}), ...])]
        for stream, entries in messages:
            for message_id, fields in entries:
                # message_id track karo — baad mein ack karenge
                self._in_flight_msg_ids.add(message_id)

                # "data" field mein JSON string hai
                raw = fields.get("data", "{}")
                result.append(json.loads(raw))

        return result

    def snapshot(self) -> MessageT:
        """
        Current state save karo — Bytewax restart pe
        yahan se resume hoga.
        RabbitMQ mein bhi yahi tha.
        """
        return self._in_flight_msg_ids

    def garbage_collect(self, state):
        """
        Successfully process hue messages ko acknowledge karo.
        
        RabbitMQ mein tha:
            channel.basic_ack(delivery_tag=msg_id)
        
        Redis mein hai:
            client.xack(stream_name, group_name, msg_id)
        
        Agar ack nahi kiya toh Redis dobara bhejega —
        same as RabbitMQ ka behavior.
        """
        closed_msg_ids = state
        for msg_id in closed_msg_ids:
            self.client.xack(
                self.stream_name,
                self.group_name,
                msg_id
            )
            self._in_flight_msg_ids.discard(msg_id)

    def close(self):
        """Connection band karo."""
        self.connection.close()


class RedisSource(FixedPartitionedSource):
    """
    RabbitMQSource ki jagah RedisSource.
    
    Bytewax isko use karta hai yeh jaanne ke liye ki
    kitne partitions hain aur har partition kaise build karna hai.
    """

    def list_parts(self) -> List[str]:
        # Abhi single partition — baad mein multiple workers ke liye
        # ["partition-0", "partition-1", ...] kar sakte hain
        return ["single-partition"]

    def build_part(
        self,
        now: datetime,
        for_part: str,
        resume_state: MessageT | None = None,
    ) -> StatefulSourcePartition[DataT, MessageT]:
        return RedisStreamPartition(
            stream_name=settings.REDIS_STREAM_NAME,  # RABBITMQ_QUEUE_NAME ki jagah
            group_name="feature-pipeline",            # consumer group naam
            consumer_name=f"worker-{for_part}",      # har partition ka alag worker
            resume_state=resume_state,
        )