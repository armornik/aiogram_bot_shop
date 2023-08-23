from aiogram.types import ReplyKeyboardMarkup

back_message = '👈 Назад'
all_right_message = '✅ Все верно'
cancel_message = '🚫 Отменить'


def back_markup():
    """Для возврата в предыдущее состояние меню"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(back_message)

    return markup


def check_markup():
    """Функция размещения клавиатуры с кнопками подтверждения и перехода на предыдущий шаг"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(back_message, all_right_message)

    return markup
