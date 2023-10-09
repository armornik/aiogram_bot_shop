from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message

from states import SosState
from filters import IsUser
from loader import dp, db


@dp.message_handler(commands='sos')
async def cmd_sos(message: Message):
    """обработчик реакции на запрос пользователя"""

    # Устанавливаем состояние, означающее, что бот ожидает получение вопроса от пользователя
    await SosState.question.set()

    await message.answer(
        'В чем суть проблемы? Опишите как можно детальнее'
        ' и администратор обязательно вам ответит.',
        reply_markup=ReplyKeyboardRemove())


@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):
    """Обработчик подтверждения, что все введено верно"""

    # Словарь контекста пополняем текстом вопроса
    async with state.proxy()as data:
        data['question'] = message.text

    await message.answer('Убедитесь, что все верно.',
                         reply_markup=submit_markup())

    # Переключаемся на следующее состояние, означающее переход к шагу подтверждения вопроса пользователем
    await SosState.next()


@dp.message_handler(
    lambda message: message.text not in [cancel_message, all_right_message],
    state=SosState.submit)
async def process_price_invalid(message: Message):
    """обработчик ввода пользователем текста вместо подтверждения вопроса"""
    await message.answer('Такого варианта не было.')


@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    """Обработчик отмены вопроса от пользователя"""
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(text=all_right_message, state=SosState.submit)
async def process_submit(message: Message, state: FSMContext):
    """Обработчик отправки запроса"""

    # Получаем идентификатор клиента
    cid = message.chat.id

    # Проверяем, что у пользователя нет активных вопросов
    if db.fetchone('SELECT * FROM questions WHERE cid=?', (cid,)) is None:

        # Опираясь на дополненный ранее словарь контекста получаем содержимое заданного вопроса и добавляем его в базу
        # данных
        async with state.proxy() as data:
            db.query('INSERT INTO questions VALUES (?, ?)',
                     (cid, data['question']))

        # Отмечаем факт отправки запроса пользователем
        await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())

    else:

        # Если у пользователя уже есть активные вопросы, сообщаем о превышении лимита заданных вопросов
        await message.answer(
            'Превышен лимит на количество задаваемых вопросов.',
            reply_markup=ReplyKeyboardRemove())

    await state.finish()
