from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

# Создаем класс-шаблон с данными, отправляемыми в запросе обратного вызова
# Нам нужно будет при нажатии на кнопки со стрелками по идентификатору товара изменять количество товара
product_cb = CallbackData('product', 'id', 'action')


def product_markup(idx, count):
    global product_cb

    # Создаем объект клавиатуры
    markup = InlineKeyboardMarkup()

    # Кнопка уменьшения количества товара в заказе. Привязываем к кнопке соответствующий обработчик (action='decrease')
    back_btn = InlineKeyboardButton('⬅️', callback_data=product_cb.new(id=idx,
                                                                       action='decrease'))

    # Отображения количества товара
    count_btn = InlineKeyboardButton(count,
                                     callback_data=product_cb.new(id=idx,
                                                                  action='count'))

    # Кнопка увеличения количества товара в заказе
    next_btn = InlineKeyboardButton('➡️', callback_data=product_cb.new(id=idx,
                                                                       action='increase'))

    # Добавляем кнопки в клавиатуру
    markup.row(back_btn, count_btn, next_btn)

    return markup
