import asyncio
from db import SessionLocal
from sqlalchemy import text

async def delete_old_delivery():
    async with SessionLocal() as session:
        sql = text("""
            DELETE FROM kb_entries 
            WHERE user_question = 'Сколько дней доставка?'
        """)
        result = await session.execute(sql)
        await session.commit()
        print(f"✅ Удалено записей: {result.rowcount}")

if __name__ == "__main__":
    asyncio.run(delete_old_delivery())
