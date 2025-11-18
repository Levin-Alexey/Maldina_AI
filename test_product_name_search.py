#!/usr/bin/env python
# test_product_name_search.py
import asyncio
from product_search import get_product_by_sku, search_product_by_name
from db import SessionLocal


test_cases = [
    # По артикулу
    ("sq168", "SKU"),
    ("45710686", "SKU"),
    # По названию
    ("лампа луна", "NAME"),
    ("коран", "NAME"),
    ("массажный матрас", "NAME"),
    ("цилиндр часы", "NAME"),
    ("вселенная", "NAME"),
]


async def main():
    async with SessionLocal() as session:
        for query, search_type in test_cases:
            if search_type == "SKU":
                product = await get_product_by_sku(session, query)
            else:
                product = await search_product_by_name(session, query)
            
            if product:
                rag_preview = (product.get('rag_text', '')[:100] + "..."
                              if product.get('rag_text') else "НЕТ")
                print(f"✓ '{query}' ({search_type})")
                print(f"  ID {product['id']}: {product['name']}")
                print(f"  RAG: {rag_preview}\n")
            else:
                print(f"✗ '{query}' ({search_type}) -> не найден\n")


if __name__ == "__main__":
    asyncio.run(main())
