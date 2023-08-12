from aiogram.types import Message, ReplyKeyboardMarkup

# Импортируем объект-диспетчер запросов. Через него мы будем настраивать дальнейшую диспетчеризацию обработчиков,
# чтобы наш бот «понимал» какой именно обработчик нужно запускать при том или ином действии
from loader import dp
from filters import IsAdmin, IsUser

# Создаем переменные с текстом надписей на кнопках клавиатуры нашего бота
catalog = '🛍️ Каталог'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'
settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'


@dp.message_handler(IsAdmin(), commands='menu')
async def admin_menu(message: Message):
    """Меню админа"""
    # selective=True - показать меню участнику, прошедшему проверку
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, orders)

    await message.answer('Меню', reply_markup=markup)


@dp.message_handler(IsUser(), commands='menu')
async def user_menu(message: Message):
    """Меню пользователя"""
    # selective=True - показать меню участнику, прошедшему проверку
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    markup.add(cart)
    markup.add(delivery_status)

    await message.answer('Меню', reply_markup=markup)
