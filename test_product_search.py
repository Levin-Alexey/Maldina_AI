import asyncio
import argparse
from typing import Optional, Dict, Any

from db import SessionLocal
from product_search import get_product_by_sku


async def lookup(sku: str) -> None:
    async with SessionLocal() as session:
        product: Optional[Dict[str, Any]] = await get_product_by_sku(session, sku)
        print(f"\nЗапрос SKU: {sku}")
        if not product:
            print("Не найдено.")
            return
        print("Найден товар:")
        print(f"  id: {product.get('id')}")
        print(f"  name: {product.get('name')}")
        print(f"  category: {product.get('category')}")
        print(f"  internal_sku: {product.get('internal_sku')}")
        print(f"  wb_sku: {product.get('wb_sku')}")
        print(f"  ozon_sku: {product.get('ozon_sku')}")
        rag_text = product.get('rag_text') or ''
        if rag_text:
            print("  Описание:")
            print(rag_text)


async def main():
    parser = argparse.ArgumentParser(description="Проверка поиска товара по SKU")
    parser.add_argument("--sku", help="SKU для поиска (internal_sku / wb_sku / ozon_sku)")
    parser.add_argument("--batch", nargs="*", help="Список SKU для пакетной проверки")
    args = parser.parse_args()

    if args.batch:
        await asyncio.gather(*(lookup(s) for s in args.batch))
    elif args.sku:
        await lookup(args.sku)
    else:
        # Интерактивный режим
        print("Введите SKU (пустая строка для выхода):")
        while True:
            sku = input("> ").strip()
            if not sku:
                break
            await lookup(sku)


if __name__ == "__main__":
    asyncio.run(main())
