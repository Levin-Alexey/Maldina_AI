from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sentence_transformers import SentenceTransformer

# Модель эмбеддингов (та же, что ты использовал при импорте kb.xlsx)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def search_kb(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Семантический поиск по базе знаний kb_entries с использованием pgvector.
    Возвращает top-N записей, отсортированных по близости к запросу.
    """

    # 1. Считаем эмбеддинг пользовательского запроса
    emb = model.encode(query).tolist()

    # 2. Ищем ближайшие записи по косинусной/евклидовой метрике (оператор <->)
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
