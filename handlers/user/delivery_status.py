from aiogram.types import Message
from loader import dp, db
from .menu import delivery_status
from filters import IsUser


@dp.message_handler(IsUser(), text=delivery_status)
async def process_delivery_status(message: Message):
    """Обработчик отображения активных заказов"""

    # Получаем список заказов по идентификатору пользователя и
    orders = db.fetchall('SELECT * FROM orders WHERE cid=?',
                         (message.chat.id,))

    if len(orders) == 0:
        await message.answer('У вас нет активных заказов.')
    else:
        # переходим к запуску функции отображения статуса заказа
        await delivery_status_answer(message, orders)


async def delivery_status_answer(message, orders):
    """обработчик отображения статуса заказа"""
    res = ''

    for order in orders:
        res += f'Заказ <b>№{order[3]}</b>'
        answer = [
            ' лежит на складе.',
            ' уже в пути!',
            ' прибыл и ждет вас на почте!'
        ]

        res += answer[0]
        res += '\n\n'

    await message.answer(res)
