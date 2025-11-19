# query_logger.py
"""
Модуль для логирования запросов пользователей в базу данных.
Записывает все запросы: успешные поиски товаров, KB, и неудачные.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional


async def log_query_analytics(
    session: AsyncSession,
    telegram_user_id: int,
    query_original: str,
    search_path: str,
    final_result_type: str,
    result_id: Optional[int] = None,
    confidence_score: Optional[float] = None,
    threshold_used: Optional[float] = None,
) -> None:
    """
    Логирует запрос пользователя в таблицу query_analytics.
    
    Args:
        session: Async SQLAlchemy сессия
        telegram_user_id: ID пользователя в Telegram
        query_original: Оригинальный запрос пользователя
        search_path: Путь поиска (например, "sku_success", "sku_failed->name_success")
        final_result_type: Тип результата ("product", "kb", "failed")
        result_id: ID найденного товара или KB записи (опционально)
        confidence_score: Distance для KB поиска (опционально)
        threshold_used: Порог distance который использовался (опционально)
    
    Examples:
        # Успешный поиск товара по SKU
        await log_query_analytics(
            session, user_id=12345, query_original="sq168",
            search_path="sku_success", final_result_type="product",
            result_id=1
        )
        
        # Успешный поиск в KB
        await log_query_analytics(
            session, user_id=12345, query_original="как вернуть товар",
            search_path="sku_failed->name_failed->kb_success",
            final_result_type="kb", result_id=42,
            confidence_score=0.15, threshold_used=2.9
        )
        
        # Неудачный поиск
        await log_query_analytics(
            session, user_id=12345, query_original="непонятный запрос",
            search_path="sku_failed->name_failed->kb_failed",
            final_result_type="failed", threshold_used=2.9
        )
    """
    query_normalized = query_original.strip().lower()
    
    sql = text(
        """
        INSERT INTO query_analytics (
            telegram_user_id,
            query_original,
            query_normalized,
            search_path,
            final_result_type,
            result_id,
            confidence_score,
            threshold_used
        )
        VALUES (
            :telegram_user_id,
            :query_original,
            :query_normalized,
            :search_path,
            :final_result_type,
            :result_id,
            :confidence_score,
            :threshold_used
        )
        """
    )
    
    await session.execute(
        sql,
        {
            "telegram_user_id": telegram_user_id,
            "query_original": query_original,
            "query_normalized": query_normalized,
            "search_path": search_path,
            "final_result_type": final_result_type,
            "result_id": result_id,
            "confidence_score": confidence_score,
            "threshold_used": threshold_used,
        },
    )
    await session.commit()
