from decouple import config

BOT_TOKEN = config('BOT_TOKEN', default='')

# Список с id администраторов
ADMINS = config('ADMINS', default=[])
