# product_search.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any, List
from sentence_transformers import SentenceTransformer
import re

# Модель эмбеддингов (та же, что при импорте kb)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def get_product_by_sku(
    session: AsyncSession, sku: str
) -> Optional[Dict[str, Any]]:
    """
    Поиск товара по артикулу (internal_sku, wb_sku, ozon_sku).
    Поддерживает множественные артикулы через запятую.
    Ищет точное совпадение с одним из артикулов в списке.
    """
    sku_clean = sku.strip()
    
    sql = text(
        """
        SELECT id, internal_sku, wb_sku, ozon_sku, name, category, rag_text
        FROM products
        WHERE :sku = ANY(string_to_array(REPLACE(internal_sku, ' ', ''), ','))
           OR :sku = ANY(string_to_array(REPLACE(wb_sku, ' ', ''), ','))
           OR :sku = ANY(string_to_array(REPLACE(ozon_sku, ' ', ''), ','))
        LIMIT 1
        """
    )
    res = await session.execute(sql, {"sku": sku_clean})
    row = res.fetchone()
    return dict(row._mapping) if row else None


async def search_product_by_name(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Поиск товара по названию (name) с использованием нечёткого поиска.
    Ищет частичное совпадение (регистронезависимое).
    """
    query_clean = query.strip().lower()
    
    sql = text(
        """
        SELECT id, internal_sku, wb_sku, ozon_sku, name, category, rag_text
        FROM products
        WHERE LOWER(name) LIKE :pattern
        ORDER BY LENGTH(name) ASC -- Сначала более короткие (вероятно, более точные) совпадения
        LIMIT :limit
        """
    )
    res = await session.execute(sql, {"pattern": f"%{query_clean}%", "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_product_semantic(
    session: AsyncSession, query: str, limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Семантический поиск товара по его эмбеддингу (embedding).
    Возвращает top-N товаров, отсортированных по близости к запросу.
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
            name,
            category,
            rag_text,
            embedding <-> CAST(:emb AS vector) AS distance
        FROM products
        ORDER BY embedding <-> CAST(:emb AS vector)
        LIMIT :limit
        """
    )

    res = await session.execute(sql, {"emb": emb_str, "limit": limit})
    rows = res.fetchall()
    return [dict(row._mapping) for row in rows]


async def search_products_hybrid(
    session: AsyncSession,
    query: str,
    limit: int = 3,
    distance_threshold: float = 3.5,
) -> List[Dict[str, Any]]:
    """
    Гибридный поиск товаров: комбинирует поиск по артикулу, семантический поиск
    и поиск по названию. Приоритет: точный артикул > семантический > по названию.
    """
    combined_results = {}  # Используем словарь для дедупликации по id

    # 1. Поиск по артикулу (самый высокий приоритет)
    sku_pattern = re.compile(r"^[a-zA-Z0-9\s,-]+$")
    if sku_pattern.fullmatch(query.strip()):
        sku_product = await get_product_by_sku(session, query)
        if sku_product:
            sku_product["search_type"] = "sku_exact"
            sku_product["priority"] = 0
            sku_product["distance"] = 0.0
            combined_results[sku_product["id"]] = sku_product

    # 2. Семантический поиск
    semantic_products = await search_product_semantic(session, query, limit * 2)
    for p in semantic_products:
        # Фильтруем по порогу distance
        if "distance" in p and p["distance"] > distance_threshold:
            continue
        if p["id"] not in combined_results:
            p["search_type"] = "semantic"
            p["priority"] = 1
            combined_results[p["id"]] = p
        else:
            # Уже есть - обновляем search_type и distance
            combined_results[p["id"]]["search_type"] += ",semantic"
            if "distance" in p:
                combined_results[p["id"]]["distance"] = min(
                    combined_results[p["id"]].get("distance", 999), p["distance"]
                )

    # 3. Поиск по названию
    name_products = await search_product_by_name(session, query, limit)
    for p in name_products:
        if p["id"] not in combined_results:
            p["search_type"] = "name_keyword"
            p["priority"] = 2
            p["distance"] = 999
            combined_results[p["id"]] = p
        else:
            combined_results[p["id"]]["search_type"] += ",name_keyword"

    # Преобразуем словарь обратно в список
    final_results = list(combined_results.values())

    # Сортировка: сначала по priority, затем по distance
    final_results.sort(
        key=lambda x: (x.get("priority", 999), x.get("distance", 999))
    )

    return final_results[:limit]
