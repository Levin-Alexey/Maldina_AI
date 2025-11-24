import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://adminmaldina:maldina123!@147.78.65.141/maldinadb"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def check():
    async with SessionFactory() as session:
        result = await session.execute(
            text("SELECT id, user_question, updated_at FROM kb_entries WHERE id IN (6, 13) ORDER BY id")
        )
        print("Проверка дат обновления записей в KB:\n")
        for row in result:
            print(f"ID={row[0]}")
            print(f"Question: {row[1][:50]}...")
            print(f"Updated: {row[2]}")
            print()


if __name__ == "__main__":
    asyncio.run(check())
