from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db.storage import DatabaseManager

from data import config

# На основе класса-конструктора Bot создаем объект бота и передаем параметрs – токен и режим форматирования сообщений.
# parse_mode означает, что сообщение будет отправлено с HTML-разметкой.
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

# В Aiogram предусмотрены бэкенды для хранения состояний между этапами взаимодействия с ботом.
# Соответствующие хранилища можно создавать с помощью различных классов-конструкторов, например, MemoryStorage.
# Он позволяет хранить все данные в оперативной памяти.
storage = MemoryStorage()

# Создаем объект диспетчера для обработки входящих сообщений и запросов. Он будет необходим для диспетчеризации запросов
dp = Dispatcher(bot, storage=storage)

# Создаем объект менеджера баз данных
db = DatabaseManager('data/database.db')
