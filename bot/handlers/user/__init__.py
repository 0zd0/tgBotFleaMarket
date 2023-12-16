from . import start
from . import ads
from . import menu

user_handlers = [
    start.router,
    *ads.routes,
    menu.router,
]
