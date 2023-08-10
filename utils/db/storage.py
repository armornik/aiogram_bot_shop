from sqlite3 import connect


class DatabaseManager:

    def __init__(self, path):
        """Создает объект соединения, выполняет запрос на включение поддержки внешних ключей. Через команду commit
        настройки фиксируются, далее создается объект-курсор.
        Через него мы будем выполнять все операции с базой данных"""
        self.conn = connect(path)

        # Включение поддержки внешних ключей
        self.conn.execute('pragma foreign_keys = on')

        # Фиксация настроек
        self.conn.commit()
        # Посредник, через который выполняются все запросы к нашей базе данных
        self.cur = self.conn.cursor()

    def create_tables(self):
        """Создаем таблицы для хранения информации по категориям, товарам, корзине, заказам,
        вопросам, поступающим от клиентов.
        path - путь до базы данных"""
        self.query(
            'CREATE TABLE IF NOT EXISTS products (idx text, title text, '
            'body text, photo blob, price int, tag text)')
        self.query(
            'CREATE TABLE IF NOT EXISTS orders (cid int, usr_name text, '
            'usr_address text, products text)')
        self.query(
            'CREATE TABLE IF NOT EXISTS cart (cid int, idx text, '
            'quantity int)')
        self.query(
            'CREATE TABLE IF NOT EXISTS categories (idx text, title text)')
        # self.query('CREATE TABLE IF NOT EXISTS wallet (cid int, balance real)')
        self.query(
            'CREATE TABLE IF NOT EXISTS questions (cid int, question text)')

    def query(self, arg, values=None):
        """Метод, позволяющий выполнять любой SQL-запрос.
        Встроенному методу execute() объекта курсора мы передаем текст запроса,
         и сохраняем результат его выполнения в базе данных."""
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        """Выполняет запрос к базе данных и получает любой объект, исходя из сути запроса."""
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        """Получает набор объектов"""
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()

    def __del__(self):
        """Закрытие подключения к базе данных"""
        self.conn.close()
