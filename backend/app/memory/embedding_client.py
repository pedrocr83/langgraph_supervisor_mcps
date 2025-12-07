import httpx
import logging
from typing import List, Sequence
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Thin async client for TEI embeddings."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.EMBEDDINGS_URL or "").rstrip("/")
        self.timeout = timeout or settings.MEMORY_TIMEOUT_SECONDS

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.base_url:
            raise ValueError("EMBEDDINGS_URL is not configured.")

        url = f"{self.base_url}/embed"
        payload = {"inputs": list(texts)}
        logger.debug("Requesting embeddings from %s for %d texts", url, len(texts))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        # TEI returns either a list or an object with "data"
        embeddings = data.get("data") if isinstance(data, dict) else data
        if embeddings is None:
            raise ValueError("Embedding response missing data.")
        if len(embeddings) != len(texts):
            raise ValueError("Embedding count mismatch.")
        return embeddings

