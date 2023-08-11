from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

from data.config import ADMINS
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

🤖 Я бот-магазин по подаже товаров одежды бренда Luvvy.

🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся 
товары возпользуйтесь командой /menu.

❓ Возникли вопросы? Не проблема! Команда /sos поможет 
связаться с админами, которые постараются как можно быстрее откликнуться.
    ''', reply_markup=markup)


@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message):
    """Выбор пользователем режима администратора"""
    cid = message.chat.id
    if cid not in ADMINS:
        await message.answer('Извините, Вас нет в списке админов')
        # ADMINS.append(cid)

    # ReplyKeyboardRemove() удаляем клавиатуру выбора режима
    await message.answer('Включен админский режим.',
                         reply_markup=ReplyKeyboardRemove())


@dp.message_handler(text=user_message)
async def user_mode(message: types.Message):
    """Выбор пользователем режима пользователя"""
    # cid = message.chat.id
    # if cid in ADMINS:
    #     ADMINS.remove(cid)

    await message.answer('Включен пользовательский режим.',
                         reply_markup=ReplyKeyboardRemove())

