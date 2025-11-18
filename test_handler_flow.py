#!/usr/bin/env python
# test_handler_flow.py
"""Симуляция логики из handlers_question.py"""
import asyncio
import re
from product_search import get_product_by_sku, search_product_by_name
from db import SessionLocal


SKU_PATTERN = re.compile(r"^[A-Za-z0-9\-_]+$")

test_queries = [
    "sq168",           # артикул -> найдёт по SKU
    "45710686",        # артикул WB -> найдёт по SKU
    "коран",           # название -> найдёт по name
    "массажный",       # название -> найдёт по name
    "лампа",           # название -> найдёт по name
    "какая доставка",  # НЕ товар -> пойдёт в KB
]


async def simulate_handler(query: str):
    print(f"\n{'='*60}")
    print(f"Запрос: '{query}'")
    print(f"{'='*60}")
    
    async with SessionLocal() as session:
        product = None
        
        # 1. Проверяем артикул
        if SKU_PATTERN.match(query):
            print("→ Похоже на артикул, ищем по SKU...")
            product = await get_product_by_sku(session, query)
            if product:
                print(f"✓ Найден товар ID {product['id']}: {product['name']}")
        
        # 2. Если не нашли - по названию
        if not product:
            print("→ Ищем по названию товара...")
            product = await search_product_by_name(session, query)
            if product:
                print(f"✓ Найден товар ID {product['id']}: {product['name']}")
        
        # 3. Результат
        if product:
            print(f"→ ОТВЕТ: показываем товар + rag_text")
            print(f"   RAG: {product.get('rag_text', 'НЕТ')[:80]}...")
        else:
            print(f"→ Товар не найден, идём в KB search...")


async def main():
    for q in test_queries:
        await simulate_handler(q)


if __name__ == "__main__":
    asyncio.run(main())
