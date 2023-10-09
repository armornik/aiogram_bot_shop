from aiogram.types import ReplyKeyboardMarkup

back_message = '👈 Назад'
all_right_message = '✅ Все верно'
cancel_message = '🚫 Отменить'
confirm_message = '✅ Подтвердить заказ'


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


def confirm_markup():
    """Функция формирования разметки для подтверждения заказа"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(confirm_message)
    markup.add(back_message)

    return markup


def submit_markup():
    """Функция для формирования разметки клавиатуры для подтверждения вопроса пользователя"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(cancel_message, all_right_message)

    return markup
