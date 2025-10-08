from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


CHANNEL_ID = -1003052677928
THREAD_ID = 2

router = Router()


class DefectStates(StatesGroup):
    waiting_message = State()


@router.callback_query(lambda c: c.data == "defect")
async def defect_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Пожалуйста, укажите название или артикул товара, подробно опишите "
        "проблему и прикрепите фото и/или видео, на которых хорошо видно "
        "проблему или брак."
    )
    await state.set_state(DefectStates.waiting_message)


@router.message(DefectStates.waiting_message)
async def defect_receive(message: types.Message, state: FSMContext):
    # Формируем подпись
    user = message.from_user
    caption = (
        f"Заявка на брак от @{user.username or user.id}\nИмя: {user.first_name or ''}"
    )
    if message.text:
        caption += f"\nСообщение: {message.text}"
    # Пересылаем все типы контента
    if message.photo:
        await message.bot.send_photo(
            CHANNEL_ID,
            message.photo[-1].file_id,
            caption=caption,
            message_thread_id=THREAD_ID,
        )
    elif message.video:
        await message.bot.send_video(
            CHANNEL_ID,
            message.video.file_id,
            caption=caption,
            message_thread_id=THREAD_ID,
        )
    elif message.document:
        await message.bot.send_document(
            CHANNEL_ID,
            message.document.file_id,
            caption=caption,
            message_thread_id=THREAD_ID,
        )
    else:
        await message.bot.send_message(CHANNEL_ID, caption, message_thread_id=THREAD_ID)
    await message.answer("Ваша заявка отправлена! Спасибо.")
    await state.clear()
