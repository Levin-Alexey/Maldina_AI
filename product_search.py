# product_search.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any

async def get_product_by_sku(session: AsyncSession, sku: str) -> Optional[Dict[str, Any]]:
    sql = text(
        """
        SELECT *
        FROM products
        WHERE internal_sku = :sku
           OR wb_sku = :sku
           OR ozon_sku = :sku
        LIMIT 1
        """
    )
    res = await session.execute(sql, {"sku": sku})
    row = res.fetchone()
    return dict(row._mapping) if row else None
