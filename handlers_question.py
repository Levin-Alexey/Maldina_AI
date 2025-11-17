# handlers_question.py (фрагмент)
from product_search import get_product_by_sku  # новый модуль
import re

SKU_PATTERN = re.compile(r"^[A-Za-z0-9\-]+$")  # упрощённо: без пробелов и спецсимволов


@router.message(QuestionStates.waiting_query)
async def handle_user_query(message: types.Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Пожалуйста, введите текст запроса.")
        return

    async with SessionLocal() as session:
        # 1. Если это похоже на артикул -> ищем товар
        if SKU_PATTERN.match(query):
            product = await get_product_by_sku(session, query)
            if product:
                # здесь можно красиво отформатировать карточку товара
                text_resp = (
                    f"Найден товар:\n"
                    f"{product['name']}\n"
                    f"Артикул: {query}\n"
                    f"Категория: {product.get('category')}\n"
                    f"{product.get('rag_text')}"
                )
                await message.answer(text_resp)
                await state.clear()
                return
        # 2. Иначе – обычный вопрос, идём в RAG по KB
        results = await search_kb(session, query, limit=3)

    if not results:
        await message.answer(
            "Ответ не найден в базе знаний. Пожалуйста, обратитесь в поддержку бота."
        )
    else:
        kb_answers = []
        for res in results:
            answer = res["answer_primary"]
            if res.get("answer_followup"):
                answer += f"\n\n{res['answer_followup']}"
            kb_answers.append(answer)
        llm_response = ask_llm(query, kb_answers)
        await message.answer(llm_response)

    await state.clear()
