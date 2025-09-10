
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Логирование
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


# Загружаем переменные окружения из .env
load_dotenv()

# Токен бота читаем из переменной окружения TELEGRAM_BOT_TOKEN
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('Не задан токен. Установите переменную окружения TELEGRAM_BOT_TOKEN или .env файл')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Первое сообщение")

async def main():
    logging.info('Bot starting...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('Bot stopped')
