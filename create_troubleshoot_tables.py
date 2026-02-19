#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для создания таблиц troubleshooting в БД
Запуск: python create_troubleshoot_tables.py
"""

import asyncio
from db import engine
from models import Base, TroubleshootInstruction, TroubleshootSession


async def create_tables():
    """Создает таблицы troubleshooting в БД"""
    print("🔧 Создание таблиц troubleshooting...")
    
    async with engine.begin() as conn:
        # Создаем только таблицы troubleshooting
        await conn.run_sync(Base.metadata.create_all, 
                           tables=[
                               TroubleshootInstruction.__table__,
                               TroubleshootSession.__table__
                           ])
    
    print("✅ Таблицы успешно созданы:")
    print("   - troubleshoot_instructions")
    print("   - troubleshoot_sessions")
    print("\n💡 Теперь можно запустить импорт данных:")
    print("   python import_instructions.py")


async def check_tables():
    """Проверяет существование таблиц"""
    from sqlalchemy import text
    from db import SessionLocal
    
    async with SessionLocal() as session:
        # Проверка troubleshoot_instructions
        result1 = await session.execute(
            text("SELECT COUNT(*) FROM troubleshoot_instructions")
        )
        count1 = result1.scalar()
        
        # Проверка troubleshoot_sessions
        result2 = await session.execute(
            text("SELECT COUNT(*) FROM troubleshoot_sessions")
        )
        count2 = result2.scalar()
        
        print(f"\n📊 Статистика таблиц:")
        print(f"   troubleshoot_instructions: {count1} записей")
        print(f"   troubleshoot_sessions: {count2} записей")


if __name__ == "__main__":
    print("=" * 60)
    print("  Создание таблиц Troubleshooting")
    print("=" * 60)
    print()
    
    asyncio.run(create_tables())
    
    # Проверяем созданные таблицы
    try:
        asyncio.run(check_tables())
    except Exception as e:
        print(f"\n⚠️  Не удалось проверить таблицы: {e}")
        print("   (Это нормально, если таблицы только что созданы и пусты)")
