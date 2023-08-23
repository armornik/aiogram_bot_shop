from aiogram.dispatcher.filters.state import StatesGroup, State


class CategoryState(StatesGroup):
    """Как только состояние будет меняться (мы ввели название категории),
    будет запускаться соответствующий обработчик"""
    title = State()


class ProductState(StatesGroup):
    """Класс для нового товара (наименование, картинка, цена, кнопка подтверждение)"""
    title = State()
    body = State()
    image = State()
    price = State()
    confirm = State()
