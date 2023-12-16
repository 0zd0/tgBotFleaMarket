from . import add
from . import my_ads
from . import actions


routes = [
    add.router,
    my_ads.router,
    *actions.routes,
]
