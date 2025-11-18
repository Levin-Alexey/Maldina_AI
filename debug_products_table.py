#!/usr/bin/env python
# debug_products_table.py
import asyncio
from sqlalchemy import text
from db import SessionLocal


async def main():
    async with SessionLocal() as session:
        # Посмотрим первые 5 записей
        sql = text("SELECT id, internal_sku, wb_sku, ozon_sku FROM products LIMIT 5")
        res = await session.execute(sql)
        rows = res.fetchall()
        
        print("=== Первые 5 строк из products ===")
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"  internal_sku: {repr(row[1])}")
            print(f"  wb_sku: {repr(row[2])}")
            print(f"  ozon_sku: {repr(row[3])}")
            print()

if __name__ == "__main__":
    asyncio.run(main())
