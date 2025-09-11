from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from kb_search import search_kb
from sqlalchemy.ext.asyncio import async_sessionmaker
from db import SessionLocal
from llm_client import ask_llm

router = Router()


class QuestionStates(StatesGroup):
    waiting_query = State()


@router.callback_query(lambda c: c.data == "question")
async def handle_question(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите артикул товара или задайте Ваш вопрос")
    await state.set_state(QuestionStates.waiting_query)


@router.message(QuestionStates.waiting_query)
async def handle_user_query(message: types.Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Пожалуйста, введите текст запроса.")
        return
    async with SessionLocal() as session:
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
