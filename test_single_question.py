import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from kb_search import search_kb

# --- Конфигурация базы данных ---
DATABASE_URL = "postgresql+asyncpg://adminmaldina:maldina123!@147.78.65.141/maldinadb"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def test_question(question: str):
    async with AsyncSessionFactory() as session:
        print(f"\n{'='*60}")
        print(f"Вопрос: {question}")
        print(f"{'='*60}\n")
        
        results = await search_kb(session, question, limit=3)
        
        if results:
            print(f"Найдено ответов: {len(results)}")
            for i, result in enumerate(results, 1):
                print(f"\n--- Ответ {i} ---")
                print(f"ID: {result.get('id')}")
                print(f"Категория: {result.get('category')}")
                print(f"Вопрос в БД: {result.get('user_question')}")
                print(f"Distance: {result.get('distance', 'N/A'):.4f}" if 'distance' in result else f"Distance: N/A")
                print(f"\nОтвет:\n{result.get('answer_primary')}")
                if result.get('answer_followup'):
                    print(f"\nДополнительно:\n{result.get('answer_followup')}")
        else:
            print("Ответы не найдены.")


if __name__ == "__main__":
    asyncio.run(test_question("когда придет заказ?"))
