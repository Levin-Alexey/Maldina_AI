# handlers_ai_troubleshoot.py
"""
Хэндлер для функции "Решить проблему с ИИ"
Пошаговая диагностика неисправностей товаров
"""

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db import SessionLocal
from troubleshoot_search import (
    search_instructions_hybrid,
    get_instruction_by_id
)
from models import TroubleshootSession
from datetime import datetime

router = Router()

# Порог релевантности для семантического поиска
DISTANCE_THRESHOLD = 3.0  # Увеличен для лучшего покрытия


class TroubleshootStates(StatesGroup):
    waiting_product = State()       # Ожидание названия/артикула товара
    selecting_issue = State()       # Выбор проблемы (если несколько)
    showing_steps = State()         # Показ шагов пошагово
    feedback = State()              # Сбор обратной связи


# ========================================================================
# КЛАВИАТУРЫ
# ========================================================================

def get_main_menu_kb():
    """Кнопка возврата в главное меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🏠 Главное меню", 
                callback_data="main_menu"
            )]
        ]
    )


def get_step_navigation_kb(current_step: int, total_steps: int, can_skip: bool = False):
    """
    Кнопки навигации по шагам
    
    Args:
        current_step: Текущий шаг (1-based)
        total_steps: Всего шагов
        can_skip: Показывать ли кнопку "Пропустить"
    """
    buttons = []
    
    # Основная кнопка действия
    if current_step < total_steps:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Готово, следующий шаг", 
                callback_data=f"step_next_{current_step}"
            )
        ])
    else:
        # Последний шаг - запрашиваем обратную связь
        buttons.append([
            InlineKeyboardButton(
                text="✅ Заработало! 🎉", 
                callback_data="step_resolved_yes"
            )
        ])
    
    # Кнопка "Не помогло"
    buttons.append([
        InlineKeyboardButton(
            text="❌ Не помогло", 
            callback_data="step_not_helped"
        )
    ])
    
    # Кнопка "Главное меню"
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню", 
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_issue_selection_kb(instructions: list):
    """
    Кнопки для выбора проблемы из нескольких вариантов
    
    Args:
        instructions: Список инструкций с полями id, issue_description
    """
    buttons = []
    
    for idx, instruction in enumerate(instructions[:5], start=1):  # Макс 5 вариантов
        issue_text = instruction['issue_description'][:50]  # Обрезаем длинные
        buttons.append([
            InlineKeyboardButton(
                text=f"{idx}. {issue_text}...", 
                callback_data=f"select_issue_{instruction['id']}"
            )
        ])
    
    # Кнопка "Другая проблема"
    buttons.append([
        InlineKeyboardButton(
            text="🔍 Другая проблема", 
            callback_data="ai_troubleshoot_restart"
        )
    ])
    
    # Кнопка "Главное меню"
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню", 
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_not_helped_kb():
    """Кнопки когда инструкция не помогла"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📞 Связаться с поддержкой", 
                callback_data="feedback"
            )],
            [InlineKeyboardButton(
                text="📦 Сообщить о браке", 
                callback_data="defect"
            )],
            [InlineKeyboardButton(
                text="🔄 Попробовать другое решение", 
                callback_data="ai_troubleshoot_restart"
            )],
            [InlineKeyboardButton(
                text="🏠 Главное меню", 
                callback_data="main_menu"
            )]
        ]
    )


# ========================================================================
# HANDLERS
# ========================================================================

@router.callback_query(lambda c: c.data == "ai_troubleshoot" or c.data == "ai_troubleshoot_restart")
async def troubleshoot_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало диагностики - запрос товара"""
    await callback.answer()
    
    # Очищаем предыдущее состояние
    await state.clear()
    
    await callback.message.answer(
        "🔧 <b>Решить проблему с ИИ</b>\n\n"
        "Я помогу вам решить проблему с товаром пошагово.\n\n"
        "Пожалуйста, укажите:\n"
        "• Артикул товара (внутренний, WB или Ozon)\n"
        "• Или название товара\n\n"
        "Например: <code>224761103</code> или <code>автомат</code>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb()
    )
    
    await state.set_state(TroubleshootStates.waiting_product)


@router.message(TroubleshootStates.waiting_product)
async def troubleshoot_search_product(message: types.Message, state: FSMContext):
    """Поиск товара по запросу пользователя"""
    query = message.text.strip()
    
    if not query:
        await message.answer("Пожалуйста, введите артикул или название товара.")
        return
    
    user_id = message.from_user.id
    
    # Сохраняем запрос в state
    await state.update_data(search_query=query)
    
    async with SessionLocal() as session:
        # Ищем инструкции (гибридный поиск)
        instructions = await search_instructions_hybrid(
            session, 
            query, 
            limit=5,
            distance_threshold=DISTANCE_THRESHOLD
        )
        
        if not instructions:
            # Ничего не найдено
            await message.answer(
                "😔 К сожалению, для этого товара нет готовой инструкции.\n\n"
                "Что вы можете сделать:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text="❓ Задать вопрос по товару", 
                            callback_data="question"
                        )],
                        [InlineKeyboardButton(
                            text="📦 Сообщить о браке", 
                            callback_data="defect"
                        )],
                        [InlineKeyboardButton(
                            text="🔄 Попробовать другой запрос", 
                            callback_data="ai_troubleshoot_restart"
                        )],
                        [InlineKeyboardButton(
                            text="🏠 Главное меню", 
                            callback_data="main_menu"
                        )]
                    ]
                )
            )
            
            # Логируем неудачный поиск
            session.add(TroubleshootSession(
                telegram_user_id=user_id,
                search_query=query,
                instruction_found=False,
                steps_completed=0
            ))
            await session.commit()
            
            await state.clear()
            return
        
        # Найдено одно или несколько решений
        if len(instructions) == 1:
            # Одна инструкция - сразу показываем шаги
            instruction = instructions[0]
            await state.update_data(
                instruction_id=instruction['id'],
                current_step=1,
                total_steps=len(instruction['steps']),
                product_name=instruction['product_name'],
                issue_description=instruction['issue_description']
            )
            
            # Логируем начало сессии
            session.add(TroubleshootSession(
                telegram_user_id=user_id,
                instruction_id=instruction['id'],
                search_query=query,
                instruction_found=True,
                steps_completed=0
            ))
            await session.commit()
            
            await show_current_step(message, state, instruction)
            await state.set_state(TroubleshootStates.showing_steps)
        
        else:
            # Несколько инструкций - предлагаем выбрать
            product_name = instructions[0]['product_name']
            
            text = (
                f"📦 Найден товар: <b>{product_name}</b>\n\n"
                f"Выберите вашу проблему:"
            )
            
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=get_issue_selection_kb(instructions)
            )
            
            # Сохраняем список инструкций в state
            await state.update_data(instructions=instructions)
            await state.set_state(TroubleshootStates.selecting_issue)


@router.callback_query(lambda c: c.data.startswith("select_issue_"))
async def troubleshoot_select_issue(callback: types.CallbackQuery, state: FSMContext):
    """Выбор проблемы из списка"""
    await callback.answer()
    
    instruction_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    async with SessionLocal() as session:
        instruction = await get_instruction_by_id(session, instruction_id)
        
        if not instruction:
            await callback.message.answer(
                "❌ Ошибка: инструкция не найдена.",
                reply_markup=get_main_menu_kb()
            )
            await state.clear()
            return
        
        # Сохраняем выбранную инструкцию
        data = await state.get_data()
        await state.update_data(
            instruction_id=instruction['id'],
            current_step=1,
            total_steps=len(instruction['steps']),
            product_name=instruction['product_name'],
            issue_description=instruction['issue_description']
        )
        
        # Логируем начало сессии
        session.add(TroubleshootSession(
            telegram_user_id=user_id,
            instruction_id=instruction['id'],
            search_query=data.get('search_query', ''),
            instruction_found=True,
            steps_completed=0
        ))
        await session.commit()
        
        await show_current_step(callback.message, state, instruction)
        await state.set_state(TroubleshootStates.showing_steps)


async def show_current_step(message: types.Message, state: FSMContext, instruction: dict = None):
    """
    Показывает текущий шаг инструкции
    
    Args:
        message: Объект сообщения
        state: FSM контекст
        instruction: Словарь с инструкцией (опционально, будет загружен из БД если не передан)
    """
    data = await state.get_data()
    current_step = data.get('current_step', 1)
    instruction_id = data.get('instruction_id')
    
    # Загружаем инструкцию из БД если не передана
    if not instruction:
        async with SessionLocal() as session:
            instruction = await get_instruction_by_id(session, instruction_id)
    
    if not instruction:
        await message.answer(
            "❌ Ошибка: инструкция не найдена.",
            reply_markup=get_main_menu_kb()
        )
        await state.clear()
        return
    
    steps = instruction['steps']
    total_steps = len(steps)
    
    # Получаем текст текущего шага
    step_text = steps.get(str(current_step), "Нет описания")
    
    # Формируем сообщение
    if current_step == 1:
        # Первый шаг - показываем заголовок
        text = (
            f"📦 <b>{instruction['product_name']}</b>\n"
            f"🔧 Проблема: <i>{instruction['issue_description']}</i>\n\n"
            f"Всего шагов: {total_steps}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 <b>Шаг {current_step} из {total_steps}:</b>\n\n"
            f"{step_text}"
        )
    else:
        text = (
            f"📍 <b>Шаг {current_step} из {total_steps}:</b>\n\n"
            f"{step_text}"
        )
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_step_navigation_kb(current_step, total_steps)
    )


@router.callback_query(lambda c: c.data.startswith("step_next_"))
async def troubleshoot_next_step(callback: types.CallbackQuery, state: FSMContext):
    """Переход к следующему шагу"""
    await callback.answer("✅ Отлично, переходим к следующему шагу!")
    
    data = await state.get_data()
    current_step = data.get('current_step', 1)
    
    # Увеличиваем счетчик шагов
    new_step = current_step + 1
    await state.update_data(current_step=new_step)
    
    # Показываем следующий шаг
    await show_current_step(callback.message, state)


@router.callback_query(lambda c: c.data == "step_resolved_yes")
async def troubleshoot_resolved(callback: types.CallbackQuery, state: FSMContext):
    """Проблема решена успешно"""
    await callback.answer("🎉 Отлично!")
    
    data = await state.get_data()
    user_id = callback.from_user.id
    instruction_id = data.get('instruction_id')
    current_step = data.get('current_step', 0)  
    search_query = data.get('search_query', '')
    
    # Логируем успешное завершение
    async with SessionLocal() as session:
        session.add(TroubleshootSession(
            telegram_user_id=user_id,
            instruction_id=instruction_id,
            search_query=search_query,
            instruction_found=True,
            steps_completed=current_step,
            issue_resolved=True,
            completed_at=datetime.now()
        ))
        await session.commit()
    
    await callback.message.answer(
        "🎉 <b>Отлично! Рад, что помог!</b>\n\n"
        "Если возникнут другие вопросы - обращайтесь!",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb()
    )
    
    await state.clear()


@router.callback_query(lambda c: c.data == "step_not_helped")
async def troubleshoot_not_helped(callback: types.CallbackQuery, state: FSMContext):
    """Шаг не помог решить проблему"""
    await callback.answer()
    
    data = await state.get_data()
    user_id = callback.from_user.id
    instruction_id = data.get('instruction_id')
    current_step = data.get('current_step', 0)
    search_query = data.get('search_query', '')
    
    # Логируем неудачу
    async with SessionLocal() as session:
        session.add(TroubleshootSession(
            telegram_user_id=user_id,
            instruction_id=instruction_id,
            search_query=search_query,
            instruction_found=True,
            steps_completed=current_step,
            issue_resolved=False,
            completed_at=datetime.now()
        ))
        await session.commit()
    
    await callback.message.answer(
        "😔 Жаль, что инструкция не помогла.\n\n"
        "Что вы можете сделать дальше:",
        reply_markup=get_not_helped_kb()
    )
    
    await state.clear()


# ========================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================================================

async def log_troubleshoot_session(
    user_id: int,
    search_query: str,
    instruction_id: int = None,
    instruction_found: bool = False,
    steps_completed: int = 0,
    issue_resolved: bool = None
):
    """Логирование сессии troubleshooting"""
    async with SessionLocal() as session:
        session.add(TroubleshootSession(
            telegram_user_id=user_id,
            instruction_id=instruction_id,
            search_query=search_query,
            instruction_found=instruction_found,
            steps_completed=steps_completed,
            issue_resolved=issue_resolved,
            completed_at=datetime.now() if issue_resolved is not None else None
        ))
        await session.commit()


# ========================================================================
# ОБРАБОТЧИК ВОЗВРАТА В ГЛАВНОЕ МЕНЮ
# ========================================================================

@router.callback_query(lambda c: c.data == "main_menu")
async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.answer()
    
    # Клавиатура главного меню (дублируем из main.py)
    menu_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вопрос по товару", callback_data="question")],
            [InlineKeyboardButton(text="Подтверждение брака", callback_data="defect")],
            [InlineKeyboardButton(text="Бонус за отзыв", callback_data="bonus")],
            [InlineKeyboardButton(text="Обратная связь", callback_data="feedback")],
            [InlineKeyboardButton(text="🤖 Решить проблему с ИИ", callback_data="ai_troubleshoot")],
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
