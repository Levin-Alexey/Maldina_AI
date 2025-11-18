# product_search.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any


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
        SELECT *
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
    session: AsyncSession, query: str
) -> Optional[Dict[str, Any]]:
    """
    Поиск товара по названию (name) с использованием нечёткого поиска.
    Ищет частичное совпадение (регистронезависимое).
    """
    query_clean = query.strip().lower()
    
    sql = text(
        """
        SELECT *
        FROM products
        WHERE LOWER(name) LIKE :pattern
        LIMIT 1
        """
    )
    res = await session.execute(sql, {"pattern": f"%{query_clean}%"})
    row = res.fetchone()
    return dict(row._mapping) if row else None
