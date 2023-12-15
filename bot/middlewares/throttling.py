from typing import Optional, Dict, MutableMapping, Callable, Any, Awaitable, cast

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.flags import extract_flags
from aiogram.types import User, TelegramObject
from cachetools import TTLCache

from bot.constants import DEFAULT_KEY_THROTTLING_MIDDLEWARE, DEFAULT_LIMIT_THROTTLING_MIDDLEWARE


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple throttling middleware using TTLCache

    Usage example:
        router.message.middleware(ThrottlingMiddleware())

    And then:
        @router.message(Command("dice"))
        @flags.rate_limit(limit=3, key='zd')
        async def dice(message: Message) -> Any:
            pass
    """

    def __init__(
            self,
            *,
            default_key: Optional[str] = DEFAULT_KEY_THROTTLING_MIDDLEWARE,
            default_limit: float = DEFAULT_LIMIT_THROTTLING_MIDDLEWARE,
            **ttl_map: float,
    ) -> None:
        """
        :param default_key: The cache key to be used by default.
        Set to None to disable throttling by default.
        :param default_limit: The TTL in default cache
        :param ttl_map: Creates additional cache instances with different TTL
        """
        self.default_key = default_key
        self.default_limit = default_limit
        self.caches: Dict[str, MutableMapping[int, None]] = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Optional[Any]:
        bot = cast(Bot, data.get('bot'))
        bot_id = bot.token.split(':')[0]
        real_handler: HandlerObject = data.get("handler")
        user: Optional[User] = data.get("event_from_user", None)
        flags: Dict[str, Any] = extract_flags(data)
        rate_limit: Dict[str, Any] = flags.get('rate_limit', {})
        key: str = (rate_limit.get('key', f'{self.default_key}_{real_handler.callback.__name__ or "message"}')
                    + f'_{bot_id}')
        limit: float = rate_limit.get('limit', self.default_limit)

        if user is not None and limit:
            if key and key in self.caches:
                if user.id in self.caches[key]:
                    return None
            else:
                self.caches[key] = TTLCache(maxsize=10_000, ttl=limit)
            self.caches[key][user.id] = None

        return await handler(event, data)
