import asyncio
import hashlib
from db import SessionLocal
from sqlalchemy import text
from sentence_transformers import SentenceTransformer

# Модель для эмбеддингов
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def add_delivery_question():
    question = "Сколько дней доставка?"
    answer = (
        "Доставка осуществляется службой логистики Wildberries. "
        "Продавец отправляет товар в день заказа, но за сроки доставки "
        "отвечает сама площадка. Уточнить срок доставки можно в личном "
        "кабинете Wildberries или в службе поддержки маркетплейса."
    )
    
    # Генерируем эмбеддинг ТОЛЬКО из вопроса (как делает поиск)
    emb = model.encode(question).tolist()
    
    # Преобразуем в строку формата '[0.123,0.456,...]' для asyncpg
    emb_str = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"
    
    # Хэш для уникальности
    source_hash = hashlib.sha256(
        (question + "\n" + answer).encode("utf-8")
    ).hexdigest()
    
    async with SessionLocal() as session:
        # Проверяем, нет ли уже такой записи
        check_sql = text(
            "SELECT id FROM kb_entries WHERE source_hash = :hash"
        )
        result = await session.execute(check_sql, {"hash": source_hash})
        if result.scalar():
            print("⚠️ Такая запись уже существует в базе!")
            return
        
        # Добавляем новую запись
        insert_sql = text("""
            INSERT INTO kb_entries (
                user_question,
                answer_primary,
                source_hash,
                embedding,
                tsv
            )
            VALUES (
                :question,
                :answer,
                :hash,
                :embedding,
                to_tsvector('russian', :search_text)
            )
        """)
        
        await session.execute(insert_sql, {
            "question": question,
            "answer": answer,
            "hash": source_hash,
            "embedding": emb_str,
            "search_text": question + " " + answer
        })
        await session.commit()
        print("✅ Запись успешно добавлена в базу знаний!")
        print(f"Вопрос: {question}")
        print(f"Ответ: {answer}")


if __name__ == "__main__":
    asyncio.run(add_delivery_question())
