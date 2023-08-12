from aiogram.types import Message
# специальный класс для создания своих классов-фильтров
from aiogram.dispatcher.filters import BoundFilter
from data.config import ADMINS


class IsUser(BoundFilter):

    async def check(self, message: Message):
        return message.from_user.id not in ADMINS
        # return message.from_user.id
