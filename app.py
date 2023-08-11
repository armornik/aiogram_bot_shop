from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from loader import dp

user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """Создаем и регистрируем асинхронный обработчик команды «start»"""

    # Создаем объект-клавиатуру. При этом включаем автоматическую подгонку под размер окна Telegram-платформы
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # Добавляем две кнопки – для включения админского и пользовательского режимов.
    # На каждой кнопке будет текст, указанный в соответствующей переменной.
    markup.row(user_message, admin_message)

    await message.answer('''Привет! 👋

🤖 Я бот-магазин по подаже товаров любой категории.

🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся 
товары возпользуйтесь командой /menu.

❓ Возникли вопросы? Не проблема! Команда /sos поможет 
связаться с админами, которые постараются как можно быстрее откликнуться.
    ''', reply_markup=markup)
