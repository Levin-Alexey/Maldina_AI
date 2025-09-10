import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# SQLAlchemy imports
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from models import Base, User

# Логирование
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)


# Загружаем переменные окружения из .env
load_dotenv()


# Токен и строка подключения к БД
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
if not BOT_TOKEN:
    raise RuntimeError("Не задан токен. Установите TELEGRAM_BOT_TOKEN или .env файл")
if not DATABASE_URL:
    raise RuntimeError("Не задана строка подключения к БД (DATABASE_URL) в .env")

# SQLAlchemy engine & session
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Клавиатура с кнопками
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Вопрос по товару", callback_data="question")],
        [InlineKeyboardButton(text="Подтверждение брака", callback_data="defect")],
        [InlineKeyboardButton(text="Бонус за отзыв", callback_data="bonus")],
        [InlineKeyboardButton(text="Обратная связь", callback_data="feedback")],
    ]
)


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Сохраняем пользователя в БД, если его нет
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )
            session.add(user)
            await session.commit()
    await message.answer("Первое сообщение", reply_markup=menu_kb)


# Обработчики кнопок

# Импортируем и регистрируем router для вопроса по товару
from handlers_question import router as question_router

dp.include_router(question_router)


# Импортируем и регистрируем router для подтверждения брака
from handlers_defect import router as defect_router

dp.include_router(defect_router)


# Импортируем и регистрируем router для бонуса за отзыв
from handlers_bonus import router as bonus_router

dp.include_router(bonus_router)


# Импортируем и регистрируем router для обратной связи
from handlers_feedback import router as feedback_router

dp.include_router(feedback_router)


async def main():
    logging.info("Bot starting...")
    # Создать таблицы, если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
