#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестирование функций поиска инструкций
Запуск: python test_troubleshoot_search.py
"""

import asyncio
from db import SessionLocal
from troubleshoot_search import (
    find_instructions_by_sku,
    search_instructions_by_product_name,
    search_instructions_semantic,
    search_instructions_hybrid,
    get_instruction_by_id
)


async def test_search_by_sku():
    """Тест поиска по артикулу"""
    print("=" * 70)
    print("ТЕСТ 1: Поиск по артикулу WB")
    print("=" * 70)
    
    async with SessionLocal() as session:
        # Из скриншота БД видим артикул WB
        results = await find_instructions_by_sku(session, "224761103")
        
        if results:
            print(f"✅ Найдено: {len(results)} инструкций")
            for r in results:
                print(f"\n   Товар: {r['product_name']}")
                print(f"   Проблема: {r['issue_description']}")
                print(f"   Шагов: {len(r['steps'])}")
        else:
            print("❌ Ничего не найдено")
    print()


async def test_search_by_name():
    """Тест поиска по названию"""
    print("=" * 70)
    print("ТЕСТ 2: Поиск по названию товара")
    print("=" * 70)
    
    async with SessionLocal() as session:
        results = await search_instructions_by_product_name(session, "автомат")
        
        if results:
            print(f"✅ Найдено: {len(results)} инструкций")
            for r in results:
                print(f"\n   Товар: {r['product_name']}")
                print(f"   Проблема: {r['issue_description']}")
        else:
            print("❌ Ничего не найдено")
    print()


async def test_search_semantic():
    """Тест семантического поиска"""
    print("=" * 70)
    print("ТЕСТ 3: Семантический поиск (по проблеме)")
    print("=" * 70)
    
    async with SessionLocal() as session:
        query = "не стреляет"
        results = await search_instructions_semantic(session, query, limit=3)
        
        if results:
            print(f"✅ Найдено: {len(results)} инструкций для '{query}'")
            for r in results:
                print(f"\n   Товар: {r['product_name']}")
                print(f"   Проблема: {r['issue_description']}")
                print(f"   Distance: {r.get('distance', 'N/A'):.3f}")
        else:
            print("❌ Ничего не найдено")
    print()


async def test_hybrid_search():
    """Тест гибридного поиска"""
    print("=" * 70)
    print("ТЕСТ 4: Гибридный поиск")
    print("=" * 70)
    
    async with SessionLocal() as session:
        # Тест 1: По артикулу
        print("\n4.1. Поиск по артикулу '224761103':")
        results = await search_instructions_hybrid(session, "224761103")
        print(f"   Найдено: {len(results)}")
        
        # Тест 2: По описанию проблемы
        print("\n4.2. Поиск по описанию 'массажер не включается':")
        results = await search_instructions_hybrid(session, "массажер не включается")
        print(f"   Найдено: {len(results)}")
        if results:
            for r in results[:3]:
                print(f"     - {r['product_name']}: {r['issue_description'][:50]}")
    print()


async def test_get_by_id():
    """Тест получения по ID"""
    print("=" * 70)
    print("ТЕСТ 5: Получение инструкции по ID")
    print("=" * 70)
    
    async with SessionLocal() as session:
        instruction = await get_instruction_by_id(session, 1)
        
        if instruction:
            print(f"✅ Инструкция ID=1:")
            print(f"   Товар: {instruction['product_name']}")
            print(f"   Проблема: {instruction['issue_description']}")
            print(f"   Шаги:")
            for step_num, step_text in instruction['steps'].items():
                print(f"     {step_num}. {step_text[:60]}...")
        else:
            print("❌ Инструкция не найдена")
    print()


async def main():
    """Запуск всех тестов"""
    print("\n")
    print("🔍 ТЕСТИРОВАНИЕ ПОИСКА ИНСТРУКЦИЙ")
    print("\n")
    
    await test_search_by_sku()
    await test_search_by_name()
    await test_search_semantic()
    await test_hybrid_search()
    await test_get_by_id()
    
    print("=" * 70)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
