from . import edit
from . import delete
from . import duplicate

routes = [
    edit.router,
    delete.router,
    duplicate.router,
]
