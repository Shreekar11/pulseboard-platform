"""EventBuffer port + Redis Streams adapter.

The buffer is abstracted behind an `EventBuffer` port so Redis Streams can be
swapped for Kafka (`acks=all`, replicated) when stronger durability / higher
throughput is required — without touching ingest or worker logic
(Phase-1-Backend §10, §14).

Producer side (ingest API): `add`.
Consumer side (worker): `ensure_group`, `read_batch`, `ack`, `autoclaim`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.config import Settings


@dataclass(slots=True)
class BufferMessage:
    """A message read from the buffer: the stream id plus its string field map."""

    id: str
    fields: dict[str, str]


class EventBuffer(ABC):
    """Port for the ingest buffer. Implementations: RedisStreamBuffer (now), Kafka (future)."""

    @abstractmethod
    async def add(self, fields: dict[str, str]) -> str:
        """Append one event; return the assigned message id."""

    @abstractmethod
    async def ensure_group(self) -> None:
        """Create the consumer group if it does not exist (idempotent)."""

    @abstractmethod
    async def read_batch(self) -> list[BufferMessage]:
        """Block-read up to a batch of new messages for this consumer."""

    @abstractmethod
    async def ack(self, ids: list[str]) -> None:
        """Acknowledge processed message ids (call ONLY after Postgres commit)."""

    @abstractmethod
    async def autoclaim(self) -> list[BufferMessage]:
        """Reclaim entries idle beyond the threshold from crashed consumers."""


class RedisStreamBuffer(EventBuffer):
    """Redis Streams implementation of EventBuffer."""

    def __init__(self, client: Redis, settings: Settings) -> None:
        self._r = client
        self._stream = settings.events_stream
        self._group = settings.consumer_group
        self._consumer = settings.consumer_name
        self._maxlen = settings.stream_maxlen
        self._batch = settings.worker_batch_size
        self._block_ms = settings.worker_block_ms
        self._claim_idle_ms = settings.worker_claim_idle_ms

    async def add(self, fields: dict[str, str]) -> str:
        # Approximate MAXLEN trim is a memory backstop only; real retention is
        # MINID-based on the consumer side so unprocessed entries are never dropped.
        return await self._r.xadd(self._stream, fields, maxlen=self._maxlen, approximate=True)

    async def ensure_group(self) -> None:
        try:
            await self._r.xgroup_create(self._stream, self._group, id="$", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def read_batch(self) -> list[BufferMessage]:
        resp: Any = await self._r.xreadgroup(
            groupname=self._group,
            consumername=self._consumer,
            streams={self._stream: ">"},
            count=self._batch,
            block=self._block_ms,
        )
        return self._flatten(resp)

    async def ack(self, ids: list[str]) -> None:
        if ids:
            await self._r.xack(self._stream, self._group, *ids)

    async def autoclaim(self) -> list[BufferMessage]:
        # XAUTOCLAIM (Redis 6.2+) reclaims idle pending entries in one call.
        _cursor, entries, _deleted = await self._r.xautoclaim(
            name=self._stream,
            groupname=self._group,
            consumername=self._consumer,
            min_idle_time=self._claim_idle_ms,
            start_id="0-0",
            count=self._batch,
        )
        return [BufferMessage(id=mid, fields=fields) for mid, fields in entries]

    @staticmethod
    def _flatten(resp: Any) -> list[BufferMessage]:
        """XREADGROUP returns [(stream, [(id, {fields}), ...])]; flatten to messages."""
        out: list[BufferMessage] = []
        if not resp:
            return out
        for _stream, entries in resp:
            for mid, fields in entries:
                out.append(BufferMessage(id=mid, fields=fields))
        return out
