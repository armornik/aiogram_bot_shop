from filters import IsUser
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatActions
from aiogram.types import ReplyKeyboardMarkup

from loader import db, dp, bot
from .menu import cart
from keyboards.inline.products_from_cart import product_markup
from keyboards.inline.products_from_catalog import product_cb


@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):
    """Отображение содержимого корзины"""

    # Получаем список позиций в корзине по идентификатору пользователя
    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))

    # Если корзина пуста, выводим соответствующее сообщение
    if len(cart_data) == 0:
        await message.answer('Ваша корзина пуста.')

    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)

        # Наполняем словарь с контекстом
        async with state.proxy() as data:
            data['products'] = {}

        # Общая стоимость заказа изначально равняется нулю
        order_cost = 0

        # Обходим содержимое корзины. Нам нужны идентификатор товара и его количество
        for _, idx, count_in_cart in cart_data:

            # Получаем объект товара по его идентификатору
            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            # Если товара уже в каталоге нет, значит нужно его удалить и из корзины
            if product is None:
                db.query('DELETE FROM cart WHERE idx=?', (idx,))

            else:
                # Раскроем содержимое объекта-товара в параметры название, описание, фото, цена
                _, title, body, image, price, _ = product

                # Увеличиваем стоимость заказа
                order_cost += price

                # Дополняем словарь параметрами очередного товара. Ключом будет идентификатор товара,
                # а значением – список с параметрами товара
                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                # Берем наш обработчик для формирования разметки карточки товара в корзине
                markup = product_markup(idx, count_in_cart)
                text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price}₽.'

                # Выводим ответ
                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        # Перейти к формированию заказа можно будет только в том, случае если стоимость товаров в корзине не равна нулю
        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Оформить заказ')

            await message.answer('Перейти к оформлению?',
                                 reply_markup=markup)


# Обработчик будет запускаться при увеличении или изменении количества товаров
@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def product_callback_handler(query: CallbackQuery, callback_data: dict,
                                   state: FSMContext):
    """обработчик изменения содержимого корзины"""

    # Из словаря контекста получаем идентификатор товара и тип действия
    idx = callback_data['id']
    action = callback_data['action']

    # Если товаров в корзине нет, т.е. корзина пуста, просто будет запущена функция process_cart()
    # и будет выведено сообщение о пустой корзине. В противном случае мы увидим количество товара
    if 'count' == action:
        async with state.proxy() as data:
            if 'products' not in data.keys():
                await process_cart(query.message, state)
            else:
                await query.answer('Количество - ' + data['products'][idx][2])

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:
                # Если же товары в корзине присутствуют, мы или увеличим, или уменьшим количество конкретного товара
                data['products'][idx][2] += 1 if 'increase' == action else -1
                # У нас будет новое количество
                count_in_cart = data['products'][idx][2]

                # Если количество равно нулю, товар из корзины просто можно убрать
                if count_in_cart == 0:
                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))
                    await query.message.delete()

                else:

                    # Иначе мы обновим количество товара в базе данных и эти изменения отразим в карточке товара
                    db.query('''UPDATE cart 
                    SET quantity = ? 
                    WHERE cid = ? AND idx = ?''',
                             (count_in_cart, query.message.chat.id, idx))

                    await query.message.edit_reply_markup(
                        product_markup(idx, count_in_cart))
