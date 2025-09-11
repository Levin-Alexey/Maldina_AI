from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any


# Поиск по базе знаний (полнотекстовый)
async def search_kb(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    sql = text(
        """
        SELECT id, category, user_question, answer_primary, answer_followup, tags, rating_context, ts_rank(tsv, plainto_tsquery('russian', :q)) AS rank
        FROM kb_entries
        WHERE tsv @@ plainto_tsquery('russian', :q)
        ORDER BY rank DESC
        LIMIT :limit
    """
    )
    res = await session.execute(sql, {"q": query, "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]
