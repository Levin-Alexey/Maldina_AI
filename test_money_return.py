import asyncio
from kb_search import search_kb
from db import SessionLocal


async def test():
    query = 'Как вернуть деньги?'
    async with SessionLocal() as session:
        results = await search_kb(session, query, limit=5)
        print(f'Запрос: {query}')
        print(f'Threshold: 2.9\n')
        for i, r in enumerate(results, 1):
            dist = r.get('distance', 0)
            status = '✅' if dist <= 2.9 else '❌'
            print(f'{i}. {status} Distance: {dist:.4f}')
            q_text = r.get('user_question', '')
            a_text = r.get('answer_primary', '')
            print(f'   Q: {q_text[:80]}')
            print(f'   A: {a_text[:100]}...\n')


asyncio.run(test())
