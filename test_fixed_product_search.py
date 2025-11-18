#!/usr/bin/env python
# test_fixed_product_search.py
import asyncio
from product_search import get_product_by_sku
from db import SessionLocal

test_cases = [
    "sq168",       # должен найти ID 1 (первый в списке)
    "sq168tat",    # тоже ID 1
    "270869273",   # ID 1 через wb_sku
    "1728614518",  # ID 1 через ozon_sku
    "qb512flash",  # ID 2
    "sq112",       # ID 3
    "45710686",    # ID 4 (wb_sku)
    "м_D5_кожа",   # ID 5
    "NOTEXIST",    # не должен найти
]

async def main():
    async with SessionLocal() as session:
        for sku in test_cases:
            product = await get_product_by_sku(session, sku)
            if product:
                print(f"✓ '{sku}' -> ID {product['id']}: {product['name']}")
            else:
                print(f"✗ '{sku}' -> не найден")

if __name__ == "__main__":
    asyncio.run(main())
