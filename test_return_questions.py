#!/usr/bin/env python
# test_return_questions.py
"""Тестирование вопросов о возврате товара"""
import asyncio
from kb_search import search_kb
from db import SessionLocal


THRESHOLD = 2.9

# Вопросы о возврате товара из скриншота
test_questions = [
    "Отказали в возврате товара",
    "Мне отказали в возврате товара, что делать?",
    "Почему мне не вернули товар?",
    "Можно ли вернуть товар, если отказали?",
    "Нет заказа",
    "Сколько дней доставка?",
    "Долгая доставка?",
    "Когда планируется доcтвка?",
    "Придет в тот день когда и указано?",
]


async def test_question(query: str):
    """Тестирует один вопрос"""
    print(f"\n{'='*70}")
    print(f"❓ Вопрос: '{query}'")
    print('='*70)
    
    async with SessionLocal() as session:
        results = await search_kb(session, query, limit=3)
        
        if not results:
            print("❌ Результатов не найдено")
            return
        
        # Проверяем лучший результат
        best = results[0]
        distance = best.get("distance", 999)
        
        print(f"\n🎯 Лучший результат (distance: {distance:.4f}):")
        if distance <= THRESHOLD:
            print("✅ ПОРОГ ПРОЙДЕН - ответ будет показан")
        else:
            print("❌ ПОРОГ НЕ ПРОЙДЕН - ответ НЕ будет показан")
        
        print(f"\nВопрос в БД: {best.get('user_question', 'N/A')}")
        print(f"Категория: {best.get('category', 'N/A')}")
        print(f"\nОтвет:")
        print(f"{best.get('answer_primary', 'N/A')}")
        
        # Показываем топ-3 для анализа
        if len(results) > 1:
            print(f"\n📊 Топ-3 результата:")
            for i, res in enumerate(results[:3], 1):
                dist = res.get("distance", 999)
                status = "✅" if dist <= THRESHOLD else "❌"
                print(f"{i}. {status} Distance: {dist:.4f}")
                print(f"   Q: {res.get('user_question', 'N/A')[:60]}...")


async def main():
    print("="*70)
    print("🧪 ТЕСТИРОВАНИЕ ВОПРОСОВ О ВОЗВРАТЕ И ДОСТАВКЕ")
    print("="*70)
    print(f"Threshold: {THRESHOLD}")
    
    for question in test_questions:
        await test_question(question)
    
    print("\n" + "="*70)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
