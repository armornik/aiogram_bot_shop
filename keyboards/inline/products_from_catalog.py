from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

product_cb = CallbackData('product', 'id', 'action')


def product_markup(idx='', price=0):
    """Разметка кнопки визуализации карточки товара"""
    global product_cb

    markup = InlineKeyboardMarkup()
    # Для каждого товара будет создана кнопка с указанием цены товара.
    # По этой кнопке мы сможем добавить товар в корзину. К кнопке привязываем обработчик добавления (action='add').
    markup.add(InlineKeyboardButton(f'Добавить в корзину - {price}₽',
                                    callback_data=product_cb.new(id=idx,
                                                                 action='add')))

    return markup
