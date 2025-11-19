#!/usr/bin/env python
# test_query_logging.py
"""Тестирование логирования запросов в query_analytics"""
import asyncio
from product_search import get_product_by_sku, search_product_by_name
from kb_search import search_kb
from query_logger import log_query_analytics
from db import SessionLocal


THRESHOLD = 2.9
TEST_USER_ID = 999999  # Тестовый ID пользователя


async def test_sku_success():
    """Тест: успешный поиск товара по SKU"""
    print("\n1️⃣ Тест: поиск товара по SKU (sq168)")
    query = "sq168"
    
    async with SessionLocal() as session:
        product = await get_product_by_sku(session, query)
        if product:
            print(f"✓ Товар найден: ID {product['id']}")
            await log_query_analytics(
                session,
                telegram_user_id=TEST_USER_ID,
                query_original=query,
                search_path="sku_success",
                final_result_type="product",
                result_id=product["id"],
            )
            print("✓ Лог записан: sku_success")
        else:
            print("✗ Товар не найден")


async def test_name_success():
    """Тест: успешный поиск товара по названию"""
    print("\n2️⃣ Тест: поиск товара по названию (массажный)")
    query = "массажный"
    
    async with SessionLocal() as session:
        product = await search_product_by_name(session, query)
        if product:
            print(f"✓ Товар найден: ID {product['id']}")
            await log_query_analytics(
                session,
                telegram_user_id=TEST_USER_ID,
                query_original=query,
                search_path="sku_failed->name_success",
                final_result_type="product",
                result_id=product["id"],
            )
            print("✓ Лог записан: sku_failed->name_success")
        else:
            print("✗ Товар не найден")


async def test_kb_success():
    """Тест: успешный поиск в базе знаний"""
    print("\n3️⃣ Тест: поиск в базе знаний (доставка)")
    query = "как доставка"
    
    async with SessionLocal() as session:
        results = await search_kb(session, query, limit=1)
        if results and results[0].get("distance", 999) <= THRESHOLD:
            best = results[0]
            print(f"✓ Ответ найден в KB: ID {best['id']}")
            print(f"  Distance: {best['distance']:.4f}")
            await log_query_analytics(
                session,
                telegram_user_id=TEST_USER_ID,
                query_original=query,
                search_path="sku_failed->name_failed->kb_success",
                final_result_type="kb",
                result_id=best["id"],
                confidence_score=best["distance"],
                threshold_used=THRESHOLD,
            )
            print("✓ Лог записан: kb_success с distance")
        else:
            print("✗ Ответ не найден в KB")


async def test_complete_failure():
    """Тест: полный провал - ничего не найдено"""
    print("\n4️⃣ Тест: полный провал (абракадабра12345)")
    query = "абракадабра12345"
    
    async with SessionLocal() as session:
        # Пробуем товар
        product = await get_product_by_sku(session, query)
        if not product:
            product = await search_product_by_name(session, query)
        
        # Пробуем KB
        results = await search_kb(session, query, limit=1)
        kb_found = (results and 
                   results[0].get("distance", 999) <= THRESHOLD)
        
        if not product and not kb_found:
            print("✓ Ничего не найдено (как и ожидалось)")
            await log_query_analytics(
                session,
                telegram_user_id=TEST_USER_ID,
                query_original=query,
                search_path="sku_failed->name_failed->kb_failed",
                final_result_type="failed",
                threshold_used=THRESHOLD,
            )
            print("✓ Лог записан: failed")
        else:
            print("✗ Что-то нашлось (неожиданно)")


async def verify_logs():
    """Проверка записанных логов в БД"""
    print("\n" + "="*60)
    print("📊 ПРОВЕРКА ЗАПИСАННЫХ ЛОГОВ")
    print("="*60)
    
    from sqlalchemy import text
    async with SessionLocal() as session:
        sql = text("""
            SELECT 
                id, query_original, search_path, final_result_type,
                result_id, confidence_score, threshold_used,
                created_at
            FROM query_analytics
            WHERE telegram_user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 10
        """)
        result = await session.execute(sql, {"user_id": TEST_USER_ID})
        rows = result.fetchall()
        
        if not rows:
            print("⚠️ Логи не найдены!")
            return
        
        print(f"\n✓ Найдено логов: {len(rows)}\n")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"  Запрос: '{row[1]}'")
            print(f"  Путь: {row[2]}")
            print(f"  Результат: {row[3]}")
            if row[4]:
                print(f"  Result ID: {row[4]}")
            if row[5] is not None:
                print(f"  Distance: {row[5]:.4f}")
            if row[6] is not None:
                print(f"  Threshold: {row[6]}")
            print(f"  Время: {row[7]}")
            print()


async def main():
    print("="*60)
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ЛОГИРОВАНИЯ ЗАПРОСОВ")
    print("="*60)
    
    await test_sku_success()
    await test_name_success()
    await test_kb_success()
    await test_complete_failure()
    
    await verify_logs()
    
    print("="*60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
