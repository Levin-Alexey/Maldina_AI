import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from kb_search import search_kb

DATABASE_URL = "postgresql+asyncpg://adminmaldina:maldina123!@147.78.65.141/maldinadb"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)

async def test():
    async with SessionFactory() as session:
        results = await search_kb(session, 'когда придет заказ?', limit=1)
        if results:
            r = results[0]
            print(f"Что получил бот (limit=1):")
            print(f"ID: {r['id']}")
            print(f"Вопрос в БД: {r['user_question']}")
            print(f"Distance: {r['distance']:.4f}")
            print(f"\nОтвет:\n{r['answer_primary']}")

if __name__ == "__main__":
    asyncio.run(test())
