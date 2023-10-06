from filters import IsUser
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatActions
import logging


from loader import db, dp, bot
from .menu import cart
from keyboards.inline.products_from_cart import product_markup
from keyboards.inline.products_from_catalog import product_cb
from keyboards.default.markups import *
from states import CheckoutState


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


@dp.message_handler(IsUser(), text='📦 Оформить заказ')
async def process_checkout(message: Message, state: FSMContext):
    """Обработчик перехода к оформлению заказа"""

    # Устанавливаем состояние проверки заказа
    await CheckoutState.check_cart.set()
    # Запускаем соответствующий обработчик
    await checkout(message, state)


async def checkout(message, state):
    """обработчик проверки содержимого заказа"""
    answer = ''
    total_price = 0

    # Опираясь на объект-состояние получаем содержимое словаря-контекста
    async with state.proxy() as data:

        # Из словаря контекста получаем параметры: название, цену товара, количество товара в корзине
        for title, price, count_in_cart in data['products'].values():

            # Вычисляем стоимость товара в корзине
            tp = count_in_cart * price
            # Формируем ответ пользователю
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}₽\n'
            # Увеличиваем общую стоимость заказа
            total_price += tp

    # Отправляем ответ пользователю
    await message.answer(f'{answer}\nОбщая сумма заказа: {total_price}₽.',
                         reply_markup=check_markup())


@dp.message_handler(IsUser(),
                    lambda message: message.text not in [all_right_message,
                                                         back_message],
                    state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    """Обработчик на тот случай, если мы отправим боту некорректное сообщение"""
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message,
                    state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    """Обработчик возврата к формированию заказа после отображения карточки заказа"""
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message,
                    state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    """Обработчик перехода к вводу имени заказчика"""
    await CheckoutState.next()
    await message.answer('Укажите свое имя.',
                         reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    """Обработчик возврата к формированию заказа после перехода к вводу имени"""
    await CheckoutState.check_cart.set()
    await checkout(message, state)


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):
    """Обработчик завершения ввода имени и перехода к вводу адреса"""

    # Работаем со словарем контекста и добавляем в него имя заказчика
    async with state.proxy() as data:

        data['name'] = message.text

        # Если адрес уже указан, запрашиваем подтверждение правильности оформления заказа и включаем
        # состояние подтверждения (confirm)
        if 'address' in data.keys():
            await confirm(message)
            await CheckoutState.confirm.set()

        # Если адрес еще не указан, предлагаем пользователю его указать и переключаемся на состояние address
        else:
            await CheckoutState.next()
            await message.answer('Укажите свой адрес места жительства.',
                                 reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):
    """обработчик возврата к вводу имени"""

    async with state.proxy() as data:

        await message.answer('Изменить имя с <b>' + data['name'] + '</b>?',
                             reply_markup=back_markup())

    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):
    """обработчик завершения ввода адреса и подтверждения заказа"""

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):
    await message.answer(
        'Убедитесь, что все правильно оформлено и подтвердите заказ.',
        reply_markup=confirm_markup())


@dp.message_handler(IsUser(),
                    lambda message: message.text not in [confirm_message,
                                                         back_message],
                    state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    """обработчик ситуации, когда при подтверждении заказа мы вводим текст"""
    await message.reply('Такого варианта не было.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    """обработчик возврата к изменению адреса"""

    await CheckoutState.address.set()

    async with state.proxy() as data:
        await message.answer('Изменить адрес с <b>' + data['address'] + '</b> на другой?',
                             reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message,
                    state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    """обработчик завершения формирования заказа"""

    markup = ReplyKeyboardRemove()

    logging.info('Deal was made.')

    async with state.proxy() as data:
        # Получаем идентификатор пользователя
        cid = message.chat.id

        # Делаем запрос к таблице с корзиной товаров, формируем массив товаров, где каждый товар представлен строкой
        # формата: 'a9cef291062dba543eb97fe5887928f0=1' Справа идентификатор товара, а слева – его количество.
        products = [idx + '=' + str(quantity)
                    for idx, quantity in db.fetchall('''SELECT idx, quantity FROM cart
        WHERE cid=?''', (cid,))]

        # Добавляем в таблицу с заказами новую запись
        db.query('INSERT INTO orders VALUES (?, ?, ?, ?)',
                 (cid, data['name'], data['address'], ' '.join(products)))

        # Удаляем запись из корзины
        db.query('DELETE FROM cart WHERE cid=?', (cid,))

        # Отправляем ответ пользователю
        await message.answer(
            'Ок! Ваш заказ уже в пути 🚀\nИмя: <b>' + data[
                'name'] + '</b>\nАдрес: <b>' + data['address'] + '</b>',
            reply_markup=markup)

    await state.finish()
