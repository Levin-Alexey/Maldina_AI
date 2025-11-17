# handlers_question.py
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from product_search import get_product_by_sku
from kb_search import search_kb
from llm_client import ask_llm
from db import SessionLocal
import re

router = Router()

SKU_PATTERN = re.compile(r"^[A-Za-z0-9\-]+$")


# Клавиатура после ответа на вопрос
question_actions_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Задать ещё вопрос", callback_data="question"
            )
        ],
        [
            InlineKeyboardButton(
                text="Вернуться в главное меню", callback_data="main_menu"
            )
        ],
    ]
)


class QuestionStates(StatesGroup):
    waiting_query = State()


@router.callback_query(lambda c: c.data == "question")
async def question_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Пожалуйста, задайте ваш вопрос или укажите артикул товара."
    )
    await state.set_state(QuestionStates.waiting_query)


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
                await message.answer(
                    text_resp, reply_markup=question_actions_kb
                )
                await state.clear()
                return
        # 2. Иначе – обычный вопрос, идём в RAG по KB
        results = await search_kb(session, query, limit=3)

    if not results:
        await message.answer(
            "Ответ не найден в базе знаний. "
            "Пожалуйста, обратитесь в поддержку бота.",
            reply_markup=question_actions_kb,
        )
    else:
        kb_answers = []
        for res in results:
            answer = res["answer_primary"]
            if res.get("answer_followup"):
                answer += f"\n\n{res['answer_followup']}"
            kb_answers.append(answer)
        llm_response = ask_llm(query, kb_answers)
        await message.answer(llm_response, reply_markup=question_actions_kb)

    await state.clear()


@router.callback_query(lambda c: c.data == "main_menu")
async def return_to_main_menu(
    callback: types.CallbackQuery, state: FSMContext
):
    """Возврат в главное меню"""
    await state.clear()
    await callback.answer()
    
    # Импортируем клавиатуру главного меню из main.py
    from main import menu_kb
    
    welcome_text = (
        "Здравствуйте! Это чат поддержки покупателей магазина MalDina.\n"
        "Здесь вы можете найти ответы на интересующие вопросы по нашим "
        "товарам, получить консультацию по возврату товара, получить бонус "
        "за отзыв, а также оставить обратную связь о нашем магазине.\n\n"
        "График работы поддержки:\n"
        "Пн - Пт с 9:00 до 18:00\n\n"
        "Для перехода в нужный раздел нажмите соответствующую кнопку:"
    )
    
    await callback.message.answer(welcome_text, reply_markup=menu_kb)
