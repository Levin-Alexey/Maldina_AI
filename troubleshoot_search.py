# troubleshoot_search.py
"""
Функции поиска инструкций по устранению неисправностей
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sentence_transformers import SentenceTransformer

# Модель эмбеддингов (та же, что при импорте)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def find_instructions_by_sku(
    session: AsyncSession, sku: str
) -> List[Dict[str, Any]]:
    """
    Поиск инструкций по артикулу (internal_sku, wb_sku, ozon_sku).
    Поддерживает множественные артикулы через запятую.
    
    Args:
        session: Асинхронная сессия БД
        sku: Артикул для поиска (строка)
    
    Returns:
        Список найденных инструкций со всеми полями
    """
    sku_clean = sku.strip()
    
    sql = text(
        """
        SELECT 
            id,
            internal_sku,
            wb_sku,
            ozon_sku,
            product_name,
            issue_description,
            steps,
            content_hash,
            created_at
        FROM troubleshoot_instructions
        WHERE 
            :sku = ANY(string_to_array(REPLACE(internal_sku, ' ', ''), ','))
            OR :sku = ANY(string_to_array(REPLACE(wb_sku, ' ', ''), ','))
            OR :sku = ANY(string_to_array(REPLACE(ozon_sku, ' ', ''), ','))
        ORDER BY created_at DESC
        """
    )
    
    res = await session.execute(sql, {"sku": sku_clean})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_instructions_by_product_name(
    session: AsyncSession, query: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Нечеткий поиск инструкций по названию товара.
    
    Args:
        session: Асинхронная сессия БД
        query: Поисковый запрос (название товара)
        limit: Максимальное количество результатов
    
    Returns:
        Список найденных инструкций
    """
    query_clean = query.strip().lower()
    
    sql = text(
        """
        SELECT 
            id,
            internal_sku,
            wb_sku,
            ozon_sku,
            product_name,
            issue_description,
            steps,
            created_at
        FROM troubleshoot_instructions
        WHERE LOWER(product_name) LIKE :pattern
        ORDER BY LENGTH(product_name) ASC
        LIMIT :limit
        """
    )
    
    res = await session.execute(
        sql, 
        {"pattern": f"%{query_clean}%", "limit": limit}
    )
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_instructions_semantic(
    session: AsyncSession, query: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Семантический поиск инструкций по эмбеддингу.
    Полезен для поиска по описанию проблемы.
    
    Args:
        session: Асинхронная сессия БД
        query: Поисковый запрос (название товара или описание проблемы)
        limit: Максимальное количество результатов
    
    Returns:
        Список найденных инструкций с distance (чем меньше, тем релевантнее)
    """
    emb = model.encode(query).tolist()
    emb_str = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"
    
    sql = text(
        """
        SELECT
            id,
            internal_sku,
            wb_sku,
            ozon_sku,
            product_name,
            issue_description,
            steps,
            embedding <-> CAST(:emb AS vector) AS distance,
            created_at
        FROM troubleshoot_instructions
        WHERE embedding IS NOT NULL
        ORDER BY embedding <-> CAST(:emb AS vector)
        LIMIT :limit
        """
    )
    
    res = await session.execute(sql, {"emb": emb_str, "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_instructions_fulltext(
    session: AsyncSession,  query: str, limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Полнотекстовый поиск по product_name и issue_description.
    Использует PostgreSQL tsvector для русского языка.
    
    Args:
        session: Асинхронная сессия БД
        query: Поисковый запрос
        limit: Максимальное количество результатов
    
    Returns:
        Список найденных инструкций с рангом релевантности
    """
    # Очищаем запрос от спецсимволов для to_tsquery
    import re
    sanitized = re.sub(r"[^\w\sа-яА-ЯёЁ]", " ", query)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    
    if not sanitized:
        return []
    
    tsquery_str = " & ".join(sanitized.split())
    
    sql = text(
        """
        SELECT
            id,
            internal_sku,
            wb_sku,
            ozon_sku,
            product_name,
            issue_description,
            steps,
            ts_rank_cd(
                to_tsvector('russian', product_name || ' ' || issue_description),
                to_tsquery('russian', :tsquery)
            ) AS rank,
            created_at
        FROM troubleshoot_instructions
        WHERE to_tsvector('russian', product_name || ' ' || issue_description) 
              @@ to_tsquery('russian', :tsquery)
        ORDER BY rank DESC
        LIMIT :limit
        """
    )
    
    res = await session.execute(
        sql, 
        {"tsquery": tsquery_str, "limit": limit}
    )
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_instructions_hybrid(
    session: AsyncSession,
    query: str,
    limit: int = 5,
    distance_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Гибридный поиск инструкций:
    1. Сначала пробуем найти по артикулу (точное совпадение)
    2. Если не нашли - используем семантический поиск
    3. Фильтруем по порогу релевантности
    
    Args:
        session: Асинхронная сессия БД
        query: Поисковый запрос (артикул или название/проблема)
        limit: Максимальное количество результатов
        distance_threshold: Порог релевантности для семантического поиска
    
    Returns:
        Список инструкций, отсортированных по релевантности
    """
    # Шаг 1: Попытка найти по артикулу
    results = await find_instructions_by_sku(session, query)
    if results:
        return results
    
    # Шаг 2: Семантический поиск
    results = await search_instructions_semantic(session, query, limit)
    
    # Фильтруем по порогу distance
    filtered = [r for r in results if r.get("distance", 1.0) <= distance_threshold]
    
    return filtered


async def get_instruction_by_id(
    session: AsyncSession, instruction_id: int
) -> Optional[Dict[str, Any]]:
    """
    Получение конкретной инструкции по ID.
    
    Args:
        session: Асинхронная сессия БД
        instruction_id: ID инструкции
    
    Returns:
        Словарь с данными инструкции или None
    """
    sql = text(
        """
        SELECT 
            id,
            internal_sku,
            wb_sku,
            ozon_sku,
            product_name,
            issue_description,
            steps,
            created_at,
            updated_at
        FROM troubleshoot_instructions
        WHERE id = :id
        """
    )
    
    res = await session.execute(sql, {"id": instruction_id})
    row = res.fetchone()
    return dict(row._mapping) if row else None


async def count_steps(steps_json: dict) -> int:
    """
    Подсчет количества шагов в JSON.
    
    Args:
        steps_json: JSON с шагами {"1": "...", "2": "..."}
    
    Returns:
        Количество шагов
    """
    return len(steps_json) if steps_json else 0
