import logging
import uuid
from typing import Iterable, List, Optional, Sequence
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SemanticMemoryEntry

logger = logging.getLogger(__name__)


class VectorStore:
    """Pgvector-backed semantic memory store."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_semantic_items(
        self,
        *,
        user_id,
        agent_id: Optional[str],
        conversation_id,
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Optional[Sequence[dict]] = None,
    ) -> None:
        if not texts or not embeddings:
            return
        if len(texts) != len(embeddings):
            raise ValueError("texts and embeddings length mismatch")
        metadatas = metadatas or [{} for _ in texts]

        rows = []
        for text, emb, meta in zip(texts, embeddings, metadatas):
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "conversation_id": conversation_id,
                    "text": text,
                    "meta": meta,
                    "embedding": list(emb),
                }
            )
        await self.session.execute(insert(SemanticMemoryEntry), rows)
        await self.session.commit()
        logger.debug("Inserted %d semantic memory rows", len(rows))

    async def search(
        self,
        *,
        query_embedding: Sequence[float],
        top_k: int,
        user_id,
        agent_id: Optional[str] = None,
        conversation_id=None,
    ) -> List[SemanticMemoryEntry]:
        distance = SemanticMemoryEntry.embedding.cosine_distance(list(query_embedding))
        stmt = (
            select(SemanticMemoryEntry, distance.label("distance"))
            .order_by(distance)
            .limit(top_k)
        )
        if user_id:
            stmt = stmt.where(SemanticMemoryEntry.user_id == user_id)
        if agent_id:
            stmt = stmt.where(SemanticMemoryEntry.agent_id == agent_id)
        if conversation_id:
            stmt = stmt.where(SemanticMemoryEntry.conversation_id == conversation_id)

        result = await self.session.execute(stmt)
        rows = result.all()
        items = []
        for entry, dist in rows:
            entry.score = 1 - float(dist) if dist is not None else None  # type: ignore[attr-defined]
            items.append(entry)
        return items

