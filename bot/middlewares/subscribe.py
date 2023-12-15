from typing import Optional, Dict, MutableMapping, Callable, Any, Awaitable, cast, Text

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.flags import extract_flags
from aiogram.enums import ChatMemberStatus
from aiogram.types import User, TelegramObject, Chat
from aiogram.utils.formatting import as_list
from cachetools import TTLCache

from bot.constants import DEFAULT_KEY_SUBSCRIBE_MIDDLEWARE, DEFAULT_LIMIT_SUBSCRIBE_MIDDLEWARE


class SubscribeChannelMiddleware(BaseMiddleware):
    """
    Usage example:
        router.message.middleware(SubscribeChannelMiddleware())

    And then:
        @router.message(Command("dice"))
        @flags.subscribe(limit=3, key='zd')
        async def dice(message: Message) -> Any:
            pass
    """

    def __init__(
            self,
            *,
            channel_id: str | int,
            default_key: Optional[str] = DEFAULT_KEY_SUBSCRIBE_MIDDLEWARE,
            default_limit: float = DEFAULT_LIMIT_SUBSCRIBE_MIDDLEWARE,
            **ttl_map: float,
    ) -> None:
        """
        :param channel_id: ID channel for sub
        :param default_key: The cache key to be used by default.
        Set to None to disable throttling by default.
        :param default_limit: The TTL in default cache
        :param ttl_map: Creates additional cache instances with different TTL
        """
        self.channel_id = channel_id
        self.default_key = default_key
        self.default_limit = default_limit
        self.caches: Dict[str, MutableMapping[int, bool]] = {}

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
        chat: Optional[Chat] = data.get("event_chat", None)
        flags: Dict[str, Any] = extract_flags(data)

        subscribe: Dict[str, Any] = flags.get('subscribe', {})
        key: str = subscribe.get('key', f'{self.default_key}_'
                                        f'_{self.channel_id}_{user.id}_{bot_id}')
        limit: float = subscribe.get('limit', self.default_limit)

        if user is not None and limit:
            if key not in self.caches:
                self.caches[key] = TTLCache(maxsize=1, ttl=limit)

            if user.id in self.caches[key]:
                check = self.caches[key][user.id]
                if not check:
                    check = await self.check_subscribe(chat, user, bot)
                    self.caches[key][user.id] = check
            else:
                check = await self.check_subscribe(chat, user, bot)
                self.caches[key][user.id] = check
            if not check:
                return None

        return await handler(event, data)

    async def send_subscribe_message(
            self,
            chat: Chat,
            bot: Bot
    ):
        sub_chat = await bot.get_chat(chat_id=self.channel_id)
        chat_username = f'@{sub_chat.username}'
        content = as_list(
            Text(f'Вы не подписаны на канал {chat_username}'),
            Text(f''),
            Text(f'Это обязательное условие для размещения объявлений.'),
            Text(f''),
            Text(f'Пожалуйста, подпишитесь на канал {chat_username} и попробуйте снова нажав /start.'),
        )
        await bot.send_message(
            chat_id=chat.id,
            text=content.as_markdown()
        )

    async def check_subscribe(
            self,
            chat: Chat,
            user: User,
            bot: Bot
    ) -> bool:
        chat_member = await bot.get_chat_member(chat_id=self.channel_id, user_id=user.id)
        if chat_member.status not in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR
        ):
            await self.send_subscribe_message(chat, bot)
            return False
        return True
