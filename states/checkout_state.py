from aiogram.dispatcher.filters.state import StatesGroup, State


class CheckoutState(StatesGroup):
    """Класс с состояниями заказа"""
    # Проверка корзины
    check_cart = State()
    # Имя
    name = State()
    # Адресс
    address = State()
    # Подтверждение
    confirm = State()
