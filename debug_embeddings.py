import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from sentence_transformers import SentenceTransformer

DATABASE_URL = "postgresql+asyncpg://adminmaldina:maldina123!@147.78.65.141/maldinadb"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def check():
    async with SessionFactory() as session:
        # Получаем вопрос и embedding из базы
        result = await session.execute(
            text("SELECT id, user_question, embedding FROM kb_entries WHERE id = 6")
        )
        row = result.fetchone()
        
        print(f"ID: {row[0]}")
        print(f"Вопрос из БД: '{row[1]}'")
        
        # Преобразуем embedding в список (может быть строкой или уже списком)
        db_emb_raw = row[2]
        if isinstance(db_emb_raw, str):
            # Убираем скобки и парсим
            db_emb = [float(x) for x in db_emb_raw.strip('[]').split(',')]
        else:
            db_emb = list(db_emb_raw)
        
        print(f"Embedding из БД (первые 5): {db_emb[:5]}")
        
        # Генерируем embedding заново
        new_emb = model.encode(row[1]).tolist()
        print(f"\nНовый embedding (первые 5): {new_emb[:5]}")
        
        # Сравниваем
        diff = sum(abs(a - b) for a, b in zip(db_emb[:10], new_emb[:10]))
        print(f"\nРазница (первые 10 элементов): {diff:.6f}")
        
        if diff < 0.001:
            print("✅ Embeddings совпадают!")
        else:
            print("❌ Embeddings РАЗНЫЕ! Что-то не так с моделью или текстом")
        
        # Проверяем distance с запросом
        query = "Когда придет заказ?"
        query_emb = model.encode(query).tolist()
        query_emb_str = "[" + ",".join(f"{x:.6f}" for x in query_emb) + "]"
        
        result = await session.execute(
            text("SELECT embedding <-> CAST(:emb AS vector) AS distance FROM kb_entries WHERE id = 6"),
            {"emb": query_emb_str}
        )
        distance = result.scalar()
        print(f"\nDistance от запроса '{query}' до ID=6: {distance:.4f}")


if __name__ == "__main__":
    asyncio.run(check())
