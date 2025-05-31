from uuid import uuid4

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from config import BOT_NAME, logger
from keyboards import get_to_main_menu_keyboard
from locales.constants_text_ru import FAQ_TEXT

router = Router()

# можно вывести в БД
FAQS = [
    {
        "question": "Как сделать заказ?",
        "answer": "Чтобы сделать заказ, перейдите в каталог и выберите товар.",
    },
    {
        "question": "Какие способы оплаты?",
        "answer": "Мы принимаем оплату картой, через YooKassa и т.д.",
    },
    {
        "question": "Как отменить заказ?",
        "answer": "Напишите в поддержку, указав номер заказа.",
    },
    {
        "question": "Сколько идет доставка?",
        "answer": "Обычно доставка занимает 2-5 рабочих дней.",
    },
]


@router.inline_query()
async def inline_faq_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    query = inline_query.query.lower()
    logger.info(
        "Пользователь ввел inline-запрос", user_id=user_id, query=query
    )

    results = []
    for faq in FAQS:
        if query in faq["question"].lower():
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=faq["question"],
                    description=faq["answer"][:50],
                    input_message_content=InputTextMessageContent(
                        message_text=f"*{faq['question']}*\n\n{faq['answer']}",
                        parse_mode="Markdown",
                    ),
                )
            )

    logger.info(
        "Inline-запрос обработан", user_id=user_id, results_found=len(results)
    )
    await inline_query.answer(results, cache_time=1)


@router.callback_query(F.data == "faq_handler")
async def faq_handler(call: CallbackQuery):
    user_id = call.from_user.id
    logger.info("Открыт раздел FAQ", user_id=user_id)

    text = FAQ_TEXT.format(BOT_NAME)
    keyboard = await get_to_main_menu_keyboard()
    await call.message.edit_text(text, reply_markup=keyboard)
