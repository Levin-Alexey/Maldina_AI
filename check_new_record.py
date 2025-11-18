import asyncio
from db import SessionLocal
from sqlalchemy import text

async def check_new_record():
    async with SessionLocal() as session:
        # Ищем запись с точным вопросом
        sql = text("""
            SELECT 
                id, 
                user_question, 
                answer_primary,
                embedding IS NOT NULL as has_embedding
            FROM kb_entries 
            WHERE user_question = 'Сколько дней доставка?'
        """)
        result = await session.execute(sql)
        row = result.fetchone()
        
        if not row:
            print("❌ Запись НЕ найдена в базе!")
        else:
            print("✅ Запись найдена:")
            print(f"ID: {row.id}")
            print(f"Вопрос: {row.user_question}")
            print(f"Ответ: {row.answer_primary}")
            print(f"Эмбеддинг: {'Есть' if row.has_embedding else 'ОТСУТСТВУЕТ!'}")

if __name__ == "__main__":
    asyncio.run(check_new_record())
