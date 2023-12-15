from pprint import pprint
from typing import Callable, Dict, Any, Optional, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class LoggerMiddleware(BaseMiddleware):
    def __init__(
            self
    ):
        pass

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Optional[Any]:
        pprint(event.model_dump())
        return await handler(event, data)
