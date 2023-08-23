# ContentType - для добавления фото
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
# Удаление категории
from aiogram.types import ReplyKeyboardRemove
# «коллбэки» - это объекты, создаваемые для кнопок и содержащие произвольное число параметров
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery
from hashlib import md5
from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatActions


from states import CategoryState, ProductState
from loader import dp, db, bot
from filters import IsAdmin
from handlers.user.menu import settings
from keyboards.default.markups import *


# При нажатии кнопки коллбек заполняется параметрами, которые мы дальше можем использовать в программе
# В данном случае category это префикс, идентифицирующий наш коллбек. Обычно этот префикс необходимо для указания,
# того, что мы работаем с какой-то конкретной клавиатурой. Например, для клавиатуры категорий один префикс,
# для клавиатуры товаров другой.
# По этому шаблону мы определяем возвращаемые данные («коллбэк-данные»). Итак, CallbackData это специальный
# фабрика-класс, позволяющий нам создать шаблон, по которому мы будем генерировать коллбэк-данные для нашего бота,
# чтобы потом на основе эти данных пользоваться другим функционалом, например,
# по id категории получать все товары для нее.
# action - для привязки другого обработчика
category_cb = CallbackData('category', 'id', 'action')

# «Коллбек» добавления в клавиатуру специальной дополнительной кнопки для удаления товара
product_cb = CallbackData('product', 'id', 'action')

cancel_message = '🚫 Отменить'
add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'
back_message = '👈 Назад'
all_right_message = '✅ Все верно'


# text=settings та кнопка, при которой запускается обработчик
@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):

    # Создаем объект клавиатуры
    markup = InlineKeyboardMarkup()

    # Делаем запрос к базе данных, получаем список категорий. Для каждой категории извлекаем идентификатор и название
    for idx, title in db.fetchall('SELECT * FROM categories'):

        # Для каждой категории создаем кнопку с названием категории. Возвращаемые данные – это идентификатор категории
        # и тип действия. Последний параметр в данном случае обозначает, что мы будем просматривать содержимое категории
        # при нажатии на кнопку с названием категории. Т.к. в возвращаемых данных есть идентификатор категории, по нему
        # будем получать список товаров категории.
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    # Размещаем в клавиатуре кнопку добавления категории. По сути коллбэкданные здесь ведут нас к запуску обработчика
    # добавления новой категории. Это похоже на то, как в Django-шаблонах мы добавляем динамические ссылки на другие
    # обработчики. Далее нам нужно будет для создать обработчик и указать, что он будет запускаться при возвращаемых
    # данных add_category, т.е. при нажатии кнопки добавления категории
    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))

    # Выводим перед пользователем надпись и блок кнопок, где каждая кнопка соответствует категории плюс одна кнопка для
    # добавления новой категории
    await message.answer('Настройка категорий:', reply_markup=markup)


# Регистрируем обработчик
@dp.callback_query_handler(IsAdmin(), text='add_category')
# Обработчик принимает объект запроса
async def add_category_callback_handler(query: CallbackQuery):
    """Обработчик обратного вызова (запроса), который мы привязали к кнопке добавления категории"""
    # Через объект запроса получаем и удаляем предыдущее сообщение в интерфейсе нашего бота
    await query.message.delete()
    # Передаем текст подсказки для ввода названия категории
    await query.message.answer('Название категории?')
    # Админ введет название категории, а мы установим состояние
    await CategoryState.title.set()


# Мы прописываем, что обработчик будет запускаться при изменении состояния – добавлении новой категории
@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):
    """Обработчик, который при изменении состояния будет выполнять добавление категории в базу данных"""

    # Т.к. админ ввел название новой категории, получаем текст сообщения, т.е. введенное название
    category = message.text
    # Идентификатором категории будет ее захешированное название
    idx = md5(category.encode('utf-8')).hexdigest()
    # Выполняем запись идентификатора и названия категории в базу данных
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    # Завершаем текущее состояние (процесс создания категории). Выключаем установленное состояние
    await state.finish()
    # Обновляем список действующих категорий
    await process_settings(message)


# метод принимает объект сообщения, список кортежей, где каждый соответствует
# определенному продукту и идентификатор категории
async def show_products(m, products, category_idx):
    """"Обработчик, который обеспечит вывод всех товаров категории"""
    # Включаем опцию печати ботом сообщения, как будто печатает живой человек
    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    # Формируем карточку
    for idx, title, body, image, price, tag in products:
        # Формируем текст в карточке товара
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        # Создаем объект клавиатуры
        markup = InlineKeyboardMarkup()
        # Добавляем в клавиатуру специальную дополнительную кнопку для удаления товара.
        # Привязываем к ней соответствующий «коллбек»
        markup.add(InlineKeyboardButton(
            '🗑️ Удалить',
            callback_data=product_cb.new(id=idx, action='delete')))

        # Отправляем ответ пользователю, где выводим фото товара и ранее сформированный текст
        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    # Формируем главное меню бота, в котором размещаем кнопку добавления товара и удаления категории
    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)

    # Выводим главное меню с дополнительной подсказкой
    await m.answer('Хотите что-нибудь добавить или удалить?',
                   reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
# Принимает объект запроса, возвращаемые данные и объект состояния
async def category_callback_handler(query: CallbackQuery, callback_data: dict,
                                    state: FSMContext):
    """Обработчик, который будет запускаться при установке action в значение view"""
    # Из словаря с возвращаемыми данными извлекаем идентификатор категории
    category_idx = callback_data['id']

    # Делаем запрос на получение всех товаров категории по ее идентифкатору
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    # Удаляем предыдущее сообщение интерфейса
    await query.message.delete()
    # Выводим новое
    await query.answer('Все добавленные товары в эту категорию.')
    # Обновляем содержимое объекта состояния новым элементом – идентификатором категории. Это будет элемент словаря
    await state.update_data(category_index=category_idx)
    # Выполняем вызов функции, которая и должна обеспечить вывод всех товаров категории
    await show_products(query.message, products, category_idx)


@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):
    """"Обработчик, который удаляет категории"""
    # Объект состояния state выполняет роль контекста в Джанго. Мы можем обратиться к содержимому контекста,
    # извлечь нужные параметры и использовать их дальше в коде.
    # Представленный выше фрагмент методом proxy() объекта состояния позволяет получить содержимое состояния
    # в виде словаря.
    async with state.proxy() as data:
        # Проверяем наличие идентификатора категории и получаем значение идентификатора по ключу из словаря
        if 'category_index' in data.keys():
            idx = data['category_index']

            # Получаем объект категории по значению идентификатора и удаляем объект категории из базы данных
            db.query(
                'DELETE FROM products WHERE tag IN (SELECT '
                'title FROM categories WHERE idx=?)',
                (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            # Удаляем клавиатуру предыдущего сообщения, отправляем сообщение «Готово»
            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            # Выводим список категорий
            await process_settings(message)


@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):
    """"Обработчик, который добавляет товар"""
    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await message.answer('Название?', reply_markup=markup)


@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):
    """"Обработчик, который отменяет добавление товара"""
    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    await process_settings(message)


# обработчик будет запускаться после изменения состояния title, т.е. когда мы введем название товара
@dp.message_handler(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):
    """Обработчик добавления описания товара после ввода названия"""

    # Передаем в словарь контекста название товара
    async with state.proxy() as data:
        data['title'] = message.text

    # Переходим к следующему состоянию, где нам будет предложено ввести описание товара
    await ProductState.next()
    # reply_markup=back_markup() - чтобы могли вернуться на предыдущий шаг
    await message.answer('Описание?', reply_markup=back_markup())


# def back_markup():
#     """Для возврата в предыдущее состояние меню"""
#     markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
#     markup.add(back_message)
#
#     return markup


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    """Обработчик возврата к добавлению товара, который будет отрабатывать только после указания названия товара"""
    await process_add_product(message)


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):
    """Обработчик изменения названия на этапе ввода описания (объект состояния body)"""
    await ProductState.title.set()

    async with state.proxy() as data:
        await message.answer(f"Изменить название с <b>{data['title']}</b>?",
                             reply_markup=back_markup())


@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):
    """Обработчик добавления фото товара после описания"""
    async with state.proxy() as data:
        # Дополняем словарь контекста описанием товара
        data['body'] = message.text

    # Переходим к следующему атрибуту-состоянию класса ProductState. Это атрибут image
    await ProductState.next()
    await message.answer('Фото?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO,
                    state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):
    """Обработчик непосредственного добавления фото и перехода к указанию цены после добавления фото"""

    # Получаем идентификатор загружаемого фото
    fileID = message.photo[-1].file_id
    # Получаем объект фото по идентификатору
    file_info = await bot.get_file(fileID)
    # Выполняем загрузку фото
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    # Пополняем словарь контекста
    async with state.proxy() as data:
        data['image'] = downloaded_file

    # Переходим к следующему состоянию и выводим соответствующее сообщение
    await ProductState.next()
    await message.answer('Цена?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(),
                    state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    """Обработчик формирования карточки товара после ввода цены"""
    async with state.proxy() as data:
        data['price'] = message.text

        title = data['title']
        body = data['body']
        price = data['price']

        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


# def check_markup():
#     """Функция размещения клавиатуры с кнопками подтверждения и перехода на предыдущий шаг"""
#     markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
#     markup.row(back_message, all_right_message)
#
#     return markup


@dp.message_handler(IsAdmin(), text=all_right_message,
                    state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    """Обработчик подтверждения регистрации товара"""
    async with state.proxy() as data:
        # запись в базу данных
        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']

        # Получаем название категории по ее идентификатору и записываем в переменную tag
        tag = db.fetchone(
            'SELECT title FROM categories WHERE idx=?',
            (data['category_index'],))[0]

        # Формируем и хешируем строку с параметрами товара, чтобы не хранить их в явном виде
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()

        # Выполняем вставку в базу данных
        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), tag))

    # Выключаем состояние и выводим соответствующую надпись
    await state.finish()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
    await process_settings(message)


@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery,
                                          callback_data: dict):
    """Обработчик обратного вызова, который мы привязали к кнопке удаления товара в методе show_products()"""
    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()


# state=ProductState.confirm - Данный обработчик срабатывает при состоянии подтверждения добавления товара
# (состояние – confirm)
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):
    """Вернуться к редактированию цены"""
    # Включаем состояние изменения цены
    await ProductState.price.set()

    async with state.proxy() as data:
        # Т.к. мы меняем цену, нам нужно знать текущее ее значение, поэтому обращаемся к словарю контекста за
        # текущим значением цены
        await message.answer(f"Изменить цену с <b>{data['price']}</b>?",
                             reply_markup=back_markup())


# С указанным обработчиком работаем, когда добавляем фото, т.е. включено соответствующее состояние
@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT,
                    state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):
    """когда мы хотим изменить описание товара или, когда вместо фото, добавили текст"""

    # Если нажимаем кнопку «Назад», включаем состояние изменения описания (body)
    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:

            # Предлагаем подтвердить изменение описания
            await message.answer(f"Изменить описание с <b>{data['body']}</b>?",
                                 reply_markup=back_markup())

    else:

        # Если вводим вместо фото текст
        await message.answer('Вам нужно прислать фото товара.')


# Обработчик будет реагировать если в качестве цены мы введем не число
@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(),
                    state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):
    """обработать ситуацию указания цены в неверном формате, например, строковом"""

    # возможность возврата к замене фото
    if message.text == back_message:

        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Другое изображение?",
                                 reply_markup=back_markup())

    else:

        await message.answer('Укажите цену в виде числа!')


@dp.message_handler(IsAdmin(),
                    lambda message: message.text not in [back_message, all_right_message],
                    state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    """если пользователь вместо подтверждения добавления товара в конце или отмены добавления напишет какой-то текст"""
    await message.answer('Такого варианта не было.')
