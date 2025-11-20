from typing import List, Dict, Any
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sentence_transformers import SentenceTransformer

# Модель эмбеддингов (та же, что при импорте kb.xlsx)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def _sanitize_query_for_tsquery(query: str) -> str:
    """Sanitizes a string for use with PostgreSQL's to_tsquery."""
    # Replace non-alphanumeric characters with spaces to allow for proper tokenization
    # and prevent syntax errors in to_tsquery.
    sanitized = re.sub(r"[^\w\sа-яА-ЯёЁ]", " ", query)
    # Replace multiple spaces with a single space
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    # Convert to tsquery format: use '&' for logical AND between words
    # and ensure no empty words if query was just punctuation.
    if not sanitized:
        return ""
    return " & ".join(sanitized.split())


async def _search_semantic(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Семантический поиск по базе знаний kb_entries с использованием pgvector.
    Возвращает top-N записей, отсортированных по близости к запросу.
    """
    emb = model.encode(query).tolist()
    emb_str = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"

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
            embedding <-> CAST(:emb AS vector) AS distance
        FROM kb_entries
        ORDER BY embedding <-> CAST(:emb AS vector)
        LIMIT :limit
        """
    )

    res = await session.execute(sql, {"emb": emb_str, "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def _search_fulltext(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Полнотекстовый поиск по базе знаний kb_entries с использованием столбца tsv.
    Возвращает top-N записей, отсортированных по релевантности.
    """
    sanitized_query = _sanitize_query_for_tsquery(query)
    if not sanitized_query:
        return []

    # Используем ts_rank_cd для ранжирования по релевантности
    # и to_tsquery('russian', ...) для запроса на русском языке
    sql = text(
        f"""
        SELECT
            id,
            category,
            user_question,
            answer_primary,
            answer_followup,
            tags,
            rating_context,
            ts_rank_cd(tsv, to_tsquery('russian', :query)) AS rank
        FROM kb_entries
        WHERE tsv @@ to_tsquery('russian', :query)
        ORDER BY rank DESC
        LIMIT :limit
        """
    )
    res = await session.execute(sql, {"query": sanitized_query, "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_kb(
    session: AsyncSession, query: str, limit: int = 3, use_hybrid_search: bool = False
) -> List[Dict[str, Any]]:
    """
    Гибридный поиск по базе знаний kb_entries.
    Может выполнять только семантический поиск или комбинировать его с полнотекстовым.
    """
    if not use_hybrid_search:
        return await _search_semantic(session, query, limit)

    # Выполняем оба типа поиска
    semantic_results = await _search_semantic(session, query, limit)
    fulltext_results = await _search_fulltext(session, query, limit)

    # Объединяем и дедуплицируем результаты
    combined_results = {}
    for res in semantic_results:
        combined_results[res['id']] = res
    for res in fulltext_results:
        # Если запись уже есть из семантического поиска, не перезаписываем
        # или можно добавить логику для объединения/переранжирования
        if res['id'] not in combined_results:
            combined_results[res['id']] = res
            
    # Преобразуем обратно в список и возвращаем
    # Здесь можно добавить более сложную логику ранжирования
    return list(combined_results.values())
