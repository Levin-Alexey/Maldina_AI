import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()


db_url = os.getenv("DATABASE_URL")
if db_url and "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "")


async def main():
    conn = await asyncpg.connect(dsn=db_url)
    print("Первые 3 записи в kb_entries:")
    rows = await conn.fetch(
        "SELECT id, user_question, answer_primary, tsv FROM kb_entries LIMIT 3"
    )
    for row in rows:
        print(dict(row))
    print("\nТест поиска по tsvector:")
    test_query = input("Введите тестовый запрос для поиска: ")
    search_sql = """SELECT id, user_question, answer_primary FROM kb_entries WHERE tsv @@ plainto_tsquery('russian', $1) LIMIT 3"""
    found = await conn.fetch(search_sql, test_query)
    for row in found:
        print(dict(row))
    if not found:
        print("По вашему запросу ничего не найдено!")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
