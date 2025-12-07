import logging
import uuid
from typing import List, Optional
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ProceduralTrace

logger = logging.getLogger(__name__)


class ProceduralMemory:
    """Procedural memory for capturing tool/step traces."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_step(
        self,
        *,
        user_id: Optional[str],
        agent_id: Optional[str],
        task_id: Optional[str],
        step: Optional[int],
        input_text: Optional[str],
        output_text: Optional[str],
        tools_used: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        try:
            await self.session.execute(
                insert(ProceduralTrace),
                [
                    {
                        "id": uuid.uuid4(),
                        "user_id": user_id,
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "step": step,
                        "input": input_text,
                        "output": output_text,
                        "tools_used": tools_used,
                        "duration_ms": duration_ms,
                    }
                ],
            )
            await self.session.commit()
        except Exception as exc:
            logger.warning("Failed to log procedural step: %s", exc)

    async def list_by_task(
        self, *, task_id: str, user_id: Optional[str] = None, limit: int = 50
    ) -> List[ProceduralTrace]:
        stmt = (
            select(ProceduralTrace)
            .where(ProceduralTrace.task_id == task_id)
            .order_by(ProceduralTrace.created_at.desc())
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(ProceduralTrace.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

