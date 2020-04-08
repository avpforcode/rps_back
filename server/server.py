from aiohttp import web
from jinja2 import FileSystemLoader
from aiohttp_jinja2 import setup as template_setup
from aiohttp_session import SimpleCookieStorage, setup as session_setup
from models import Arena, Games
from views import MainWSView, init_handler


# В качестве сервера простой websocket на базе aiohttp
app = web.Application()

# подключаем куки сессии (без шифрования) и шаблонизатор
session_setup(app, SimpleCookieStorage(cookie_name = "AIOHTTP_SESSION"))
template_setup(app, loader = FileSystemLoader('static/'))

# Вместо базы данных будем использовать
# 2-а больших кеширующих объекта, в
# первом хранятся данные всех игроков,
# во втором данные по всем текущим играм.
setattr(app, 'arena', Arena())
setattr(app, 'games', Games())

# первый маршрут загружает index и js + создает сессии
# второй обрабатывает websocket сообщения
app.add_routes([
  web.get('/', init_handler, name = 'index'),
  web.get('/ws', MainWSView, name = 'ws'),
  web.static('/static', 'static')
])

web.run_app(app, port = 3560)
