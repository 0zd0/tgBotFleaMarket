from . import start
from . import ads

user_handlers = [
    start.router,
    *ads.routes,
]
