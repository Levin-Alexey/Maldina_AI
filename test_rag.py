import asyncio
from db import SessionLocal
from kb_search import search_kb
from llm_client import ask_llm

async def test_rag(query: str):
    async with SessionLocal() as session:
        results = await search_kb(session, query, limit=1)
        print(f"\nВопрос: {query}")
        if not results:
            print("KB: ничего не найдено!")
            llm_response = ask_llm(query, [])
            print(f"LLM (без контекста): {llm_response}")
        else:
            kb_answers = []
            for res in results:
                distance = res.get("distance", "N/A")
                answer = res["answer_primary"]
                if res.get("answer_followup"):
                    answer += f"\n\n{res['answer_followup']}"
                kb_answers.append(answer)
                print(f"KB (distance={distance:.4f}):")
                print(f"  {answer}")
            llm_response = ask_llm(query, kb_answers)
            print(f"LLM: {llm_response}")

async def main():
    test_questions = [
       
        "Сколько дней доставка?"
        
    ]
    await asyncio.gather(*(test_rag(q) for q in test_questions))

if __name__ == "__main__":
    asyncio.run(main())
