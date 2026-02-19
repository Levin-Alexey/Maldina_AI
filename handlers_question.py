# handlers_question.py
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from product_search import get_product_by_sku, search_product_by_name
from kb_search import search_kb
from llm_client import ask_llm
from db import SessionLocal
from query_logger import log_query_analytics
import re

router = Router()

SKU_PATTERN = re.compile(r"^[A-Za-z0-9\-_]+$")
THRESHOLD = 3.25  # оптимальный порог на основе тестов


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
                text="Сообщить о браке", callback_data="defect"
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

    user_id = message.from_user.id
    async with SessionLocal() as session:
        product = None
        search_path_parts = []
        
        # 1. Сначала пробуем поиск по артикулу (если похоже на SKU)
        if SKU_PATTERN.match(query):
            product = await get_product_by_sku(session, query)
            if product:
                search_path_parts.append("sku_success")
                # Логируем успешный поиск по SKU
                await log_query_analytics(
                    session,
                    telegram_user_id=user_id,
                    query_original=query,
                    search_path="->".join(search_path_parts),
                    final_result_type="product",
                    result_id=product["id"],
                )
            else:
                search_path_parts.append("sku_failed")
        
        # 2. Если не нашли по артикулу - пробуем по названию
        if not product:
            product = await search_product_by_name(session, query)
            if product:
                search_path_parts.append("name_success")
                # Логируем успешный поиск по названию
                await log_query_analytics(
                    session,
                    telegram_user_id=user_id,
                    query_original=query,
                    search_path="->".join(search_path_parts),
                    final_result_type="product",
                    result_id=product["id"],
                )
            else:
                search_path_parts.append("name_failed")
        
        # 3. Если товар найден - показываем его описание
        if product:
            text_resp = (
                f"Найден товар:\n\n"
                f"📦 {product['name']}\n"
                f"🏷️ Категория: {product.get('category', 'Не указана')}\n\n"
                f"{product.get('rag_text', '')}"
            )
            await message.answer(
                text_resp, reply_markup=question_actions_kb
            )
            await state.clear()
            return
        
        # 4. Если товар не найден - идём в RAG по KB
        results = await search_kb(session, query, limit=3)

    # Проверяем единственный результат по порогу релевантности
    if not results or results[0].get("distance", 1.0) > THRESHOLD:
        # Нет релевантного ответа — логируем провал
        search_path_parts.append("kb_failed")
        async with SessionLocal() as session:
            await log_query_analytics(
                session,
                telegram_user_id=user_id,
                query_original=query,
                search_path="->".join(search_path_parts),
                final_result_type="failed",
                threshold_used=THRESHOLD,
            )
        
        await message.answer(
            "К сожалению, я не нашёл ответа на ваш вопрос в базе знаний.\n"
            "Пожалуйста, обратитесь в поддержку магазина — "
            "мы обязательно вам поможем!",
            reply_markup=question_actions_kb,
        )
    else:
        # Есть релевантные ответы — фильтруем по порогу и отправляем в LLM
        relevant_results = [r for r in results if r.get("distance", 999) <= THRESHOLD]
        
        if not relevant_results:
            # Все результаты за порогом
            search_path_parts.append("kb_failed")
            async with SessionLocal() as session:
                await log_query_analytics(
                    session,
                    telegram_user_id=user_id,
                    query_original=query,
                    search_path="->".join(search_path_parts),
                    final_result_type="failed",
                    threshold_used=THRESHOLD,
                )
            await message.answer(
                "К сожалению, я не нашёл ответа на ваш вопрос в базе знаний.\n"
                "Пожалуйста, обратитесь в поддержку магазина — "
                "мы обязательно вам поможем!",
                reply_markup=question_actions_kb,
            )
        else:
            # Используем лучший результат для логирования
            best = relevant_results[0]
            search_path_parts.append("kb_success")
            
            # Логируем успешный поиск в KB
            async with SessionLocal() as session:
                await log_query_analytics(
                    session,
                    telegram_user_id=user_id,
                    query_original=query,
                    search_path="->".join(search_path_parts),
                    final_result_type="kb",
                    result_id=best["id"],
                    confidence_score=best.get("distance"),
                    threshold_used=THRESHOLD,
                )
            
            # Собираем все релевантные ответы для LLM
            all_answers = []
            for r in relevant_results:
                answer = r["answer_primary"]
                if r.get("answer_followup"):
                    answer += f"\n\n{r['answer_followup']}"
                all_answers.append(answer)
            
            llm_response = ask_llm(query, all_answers)
            await message.answer(llm_response, reply_markup=question_actions_kb)

    await state.clear()


@router.callback_query(lambda c: c.data == "main_menu")
async def return_to_main_menu(
    callback: types.CallbackQuery, state: FSMContext
):
    """Возврат в главное меню"""
    await state.clear()
    await callback.answer()
    
    # Клавиатура главного меню
    # (дублируем из main.py, чтобы избежать циклического импорта)
    menu_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Вопрос по товару", callback_data="question"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Подтверждение брака", callback_data="defect"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Бонус за отзыв", callback_data="bonus"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Обратная связь", callback_data="feedback"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 Решить проблему с ИИ", callback_data="ai_troubleshoot"
                )
            ],
        ]
    )
    
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
