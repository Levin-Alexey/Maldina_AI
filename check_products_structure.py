#!/usr/bin/env python
# check_products_structure.py
import asyncio
from sqlalchemy import text
from db import SessionLocal


async def main():
    async with SessionLocal() as session:
        # Структура таблицы
        sql = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'products'
            ORDER BY ordinal_position
        """)
        res = await session.execute(sql)
        columns = res.fetchall()
        
        print("=== Структура таблицы products ===")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        print("\n=== Первые 3 записи ===")
        sql2 = text("""
            SELECT id, internal_sku, wb_sku, ozon_sku, 
                   name, short_name, category 
            FROM products LIMIT 3
        """)
        res2 = await session.execute(sql2)
        rows = res2.fetchall()
        
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"  internal_sku: {repr(row[1])}")
            print(f"  wb_sku: {repr(row[2])}")
            print(f"  ozon_sku: {repr(row[3])}")
            print(f"  name: {repr(row[4])}")
            print(f"  short_name: {repr(row[5])}")
            print(f"  category: {repr(row[6])}")


if __name__ == "__main__":
    asyncio.run(main())
