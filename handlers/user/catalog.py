from filters import IsUser
from aiogram.types import Message
from aiogram.types import CallbackQuery
from loader import db
from loader import bot
from aiogram.types.chat import ChatActions

from keyboards.inline.products_from_catalog import product_markup, product_cb
from keyboards.inline.categories import category_cb, categories_markup
from .menu import catalog
from loader import dp


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    """Обработчкик вывода каталога категорий для пользователя"""
    await message.answer('Выберите раздел, чтобы вывести список товаров:',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):
    """обработчик перехода к выводу всех товаров категории"""

    # делаем запрос к базе данных и получаем список товаров категории по ее идентификатору
    # categories.py - формировали словарь callback_data с возвращаемыми данными. Там есть и идентификатор категории
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Все доступные товары.')
    await show_products(query.message, products)


async def show_products(m, products):

    # Если товаров в каталоге нет, то выведем соответствующее сообщение
    if len(products) == 0:

        await m.answer('Здесь ничего нет 😢')

    else:

        # Включаем имитацию печати человеком
        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        # Для каждого товара получаем идентификатор категории, название товара, описание, фото, цену
        for idx, title, body, image, price, _ in products:

            # Формируем разметку кнопки добавления товара в корзину
            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}'

            # Выводим карточку товара с фото, названием и кнопкой добавления
            await m.answer_photo(photo=image,
                                 caption=text,
                                 reply_markup=markup)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery,
                                       callback_data: dict):
    """обработчик добавления товара в корзину"""

    # Для пользователя с текущим идентификатором выполняем добавление записи в таблицу с корзиной товаров.
    # Также, опираясь на словарь контекста (callback_data['id']), указываем идентификатор товара
    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Товар добавлен в корзину!')
    await query.message.delete()
