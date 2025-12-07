import asyncio
import uuid

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from app.memory.semantic_memory import SemanticMemory
from app.memory.procedural_memory import ProceduralMemory


async def main():
    conv_id = uuid.uuid4()
    user_email = "memory@test.local"
    user_id = None
    async with AsyncSessionLocal() as session:
        # Ensure a user + conversation exist (reuse same user if present)
        res = await session.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": user_email}
        )
        row = res.scalar_one_or_none()
        if row:
            user_id = row
        else:
            user_id = uuid.uuid4()
            await session.execute(
                text(
                    """
                    INSERT INTO users (id, email, hashed_password, is_active, is_superuser, is_verified)
                    VALUES (:id, :email, :pwd, true, false, false)
                    """
                ),
                {"id": user_id, "email": user_email, "pwd": "dummy"},
            )
            await session.commit()

        await session.execute(
            text(
                """
                INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                VALUES (:cid, :uid, 'Memory Test', now(), now())
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"cid": conv_id, "uid": user_id},
        )
        await session.commit()
        semantic = SemanticMemory(session)
        procedural = ProceduralMemory(session)

        print(f"Using conversation_id={conv_id}")

        # Write semantic entries
        await semantic.remember(
            ["hello world", "agent reply"],
            user_id=user_id,
            agent_id="supervisor",
            conversation_id=conv_id,
            metadatas=[{"role": "user"}, {"role": "assistant"}],
        )
        hits = await semantic.retrieve(
            "hello",
            user_id=user_id,
            agent_id="supervisor",
            conversation_id=conv_id,
            top_k=3,
        )
        print(f"Semantic hits: {len(hits)}")
        for hit in hits:
            print("-", hit.text[:80], getattr(hit, "score", None))

        # Log procedural step
        await procedural.log_step(
            user_id=str(user_id),
            agent_id="subagent",
            task_id=str(conv_id),
            step=1,
            input_text="input text",
            output_text="output text",
            tools_used={"tool": "demo"},
            duration_ms=123,
        )
        steps = await procedural.list_by_task(task_id=str(conv_id), user_id=str(user_id), limit=5)
        print(f"Procedural steps: {len(steps)}")
        for step in steps:
            print("-", step.step, step.input, step.output)


if __name__ == "__main__":
    asyncio.run(main())

