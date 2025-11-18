import asyncio
from db import SessionLocal
from sqlalchemy import text

async def check_delivery():
    async with SessionLocal() as session:
        # Поиск записей про доставку
        sql = text("""
            SELECT id, user_question, answer_primary 
            FROM kb_entries 
            WHERE answer_primary ILIKE '%доставк%' 
               OR user_question ILIKE '%доставк%'
            LIMIT 10
        """)
        result = await session.execute(sql)
        rows = result.fetchall()
        
        if not rows:
            print("❌ В базе знаний НЕТ записей про доставку!")
        else:
            print(f"✅ Найдено {len(rows)} записей про доставку:\n")
            for row in rows:
                print(f"ID: {row.id}")
                print(f"Вопрос: {row.user_question}")
                print(f"Ответ: {row.answer_primary[:200]}...")
                print("-" * 80)

if __name__ == "__main__":
    asyncio.run(check_delivery())
