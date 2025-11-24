import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from kb_search import search_kb
from llm_client import ask_llm

DATABASE_URL = "postgresql+asyncpg://adminmaldina:maldina123!@147.78.65.141/maldinadb"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)

THRESHOLD = 3.1

async def test():
    async with SessionFactory() as session:
        question = "Когда придет заказ?"
        print(f"Вопрос: {question}\n")
        
        results = await search_kb(session, question, limit=3)
        
        print(f"Всего найдено: {len(results)}")
        relevant_results = [r for r in results if r.get("distance", 999) <= THRESHOLD]
        print(f"Релевантных (distance <= {THRESHOLD}): {len(relevant_results)}\n")
        
        for i, r in enumerate(results, 1):
            status = "✅ PASS" if r.get("distance", 999) <= THRESHOLD else "❌ FAIL"
            print(f"{i}. ID={r['id']}, Distance={r['distance']:.4f} {status}")
            print(f"   Вопрос: {r['user_question']}")
            print()
        
        if relevant_results:
            print("\n=== Что отправляется в LLM ===\n")
            all_answers = []
            for i, r in enumerate(relevant_results, 1):
                answer = r["answer_primary"]
                if r.get("answer_followup"):
                    answer += f"\n\n{r['answer_followup']}"
                all_answers.append(answer)
                print(f"{i}. {answer[:100]}...")
            
            print("\n=== Ответ LLM ===\n")
            llm_response = ask_llm(question, all_answers)
            print(llm_response)
        else:
            print("❌ Нет релевантных результатов для отправки в LLM")

if __name__ == "__main__":
    asyncio.run(test())
