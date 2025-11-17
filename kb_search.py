# kb_search.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer

# Глобальная модель (один раз грузится при импорте модуля)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def search_kb(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Семантический поиск по базе знаний kb_entries с использованием pgvector.
    """
    # 1. Считаем эмбеддинг запроса
    emb = model.encode(query).tolist()

    # 2. SQL-запрос по вектору
    sql = text(
        """
        SELECT
            id,
            category,
            user_question,
            answer_primary,
            answer_followup,
            tags,
            rating_context,
            embedding <-> :emb::vector AS distance
        FROM kb_entries
        ORDER BY embedding <-> :emb::vector
        LIMIT :limit
        """
    )
    res = await session.execute(sql, {"emb": emb, "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]
