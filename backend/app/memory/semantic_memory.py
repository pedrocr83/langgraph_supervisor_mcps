import logging
from typing import List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.memory.embedding_client import EmbeddingClient
from app.memory.vector_store import VectorStore
from app.db.models import SemanticMemoryEntry

logger = logging.getLogger(__name__)


class SemanticMemory:
    """Semantic memory manager for supervisor."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_client: Optional[EmbeddingClient] = None,
    ):
        self.session = session
        self.embedding_client = embedding_client or EmbeddingClient()
        self.store = VectorStore(session)

    async def retrieve(
        self,
        query_text: str,
        *,
        user_id,
        agent_id: Optional[str],
        conversation_id,
        top_k: Optional[int] = None,
    ) -> List[SemanticMemoryEntry]:
        if not settings.MEMORY_ENABLE:
            return []
        try:
            query_embedding = (await self.embedding_client.embed([query_text]))[0]
            return await self.store.search(
                query_embedding=query_embedding,
                top_k=top_k or settings.MEMORY_TOP_K,
                user_id=user_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
            )
        except Exception as exc:
            logger.warning("Semantic memory retrieval failed: %s", exc)
            return []

    async def remember(
        self,
        texts: Sequence[str],
        *,
        user_id,
        agent_id: Optional[str],
        conversation_id,
        metadatas: Optional[Sequence[dict]] = None,
    ) -> None:
        if not settings.MEMORY_ENABLE or not texts:
            return
        # Truncate and chunk to avoid oversized payloads to TEI
        trimmed = [t[: settings.MEMORY_MAX_CHARS] for t in texts]
        chunk_size = max(100, settings.MEMORY_CHUNK_SIZE)
        chunked_texts = []
        chunked_metas = []
        metadatas = metadatas or [{} for _ in trimmed]

        for idx, (text, meta) in enumerate(zip(trimmed, metadatas)):
            if not text:
                continue
            for j in range(0, len(text), chunk_size):
                chunk = text[j : j + chunk_size]
                chunked_texts.append(chunk)
                chunk_meta = dict(meta)
                chunk_meta.update({"orig_index": idx, "chunk": j // chunk_size})
                chunked_metas.append(chunk_meta)

        if not chunked_texts:
            return
        try:
            embeddings = await self.embedding_client.embed(chunked_texts)
            await self.store.add_semantic_items(
                user_id=user_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                texts=chunked_texts,
                embeddings=embeddings,
                metadatas=chunked_metas,
            )
        except Exception as exc:
            logger.warning("Semantic memory write failed: %s", exc)

