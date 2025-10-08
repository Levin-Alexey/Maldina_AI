from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

CHANNEL_ID = -1003052677928
THREAD_ID = 6

router = Router()


class FeedbackStates(StatesGroup):
    waiting_message = State()


@router.callback_query(lambda c: c.data == "feedback")
async def feedback_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Здесь можно оставить отзыв о взаимодействии с чатом поддержки или "
        "Ваши пожелания. Будем рады получить честную оценку нашей работы."
    )
    await state.set_state(FeedbackStates.waiting_message)


@router.message(FeedbackStates.waiting_message)
async def feedback_receive(message: types.Message, state: FSMContext):
    user = message.from_user
    caption = (
        f"Обратная связь от @{user.username or user.id}\nИмя: {user.first_name or ''}"
    )
    if message.text:
        caption += f"\nСообщение: {message.text}"
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
    await message.answer("Ваше сообщение отправлено! Спасибо за обратную связь.")
    await state.clear()
