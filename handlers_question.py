from aiogram import types, Router

router = Router()


@router.callback_query(lambda c: c.data == "question")
async def handle_question(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Введите артикул товара или задайте Ваш вопрос")
