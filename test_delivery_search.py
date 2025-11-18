import asyncio
from db import SessionLocal
from kb_search import search_kb

async def test_delivery_search():
    query = "Сколько дней доставка?"
    async with SessionLocal() as session:
        # Ищем топ-5, чтобы увидеть все варианты
        results = await search_kb(session, query, limit=5)
        print(f"Поиск для: '{query}'\n")
        for i, res in enumerate(results, 1):
            distance = res.get("distance", "N/A")
            question = res.get("user_question", "N/A")
            answer = res["answer_primary"][:150]
            print(f"{i}. distance={distance:.4f}")
            print(f"   Вопрос: {question}")
            print(f"   Ответ: {answer}...")
            print()

if __name__ == "__main__":
    asyncio.run(test_delivery_search())
