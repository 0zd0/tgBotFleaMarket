from typing import Callable, Dict, Any, Optional, Awaitable, cast

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import TelegramObject, User, Message, CallbackQuery

from bot.db.user.model import UserModel


class UserMiddleware(BaseMiddleware):
    key = 'user'

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
        event_from_user = cast(User, data.get("event_from_user"))
        change_last_activity = False
        if isinstance(event, Message):
            if event.chat.type in (
                ChatType.PRIVATE
            ):
                change_last_activity = True
        elif isinstance(event, CallbackQuery):
            change_last_activity = True
        user, is_create = await UserModel.create_or_update(
            tg_id=event_from_user.id,
            name=event_from_user.full_name,
            username=event_from_user.username,
            change_last_activity=change_last_activity
        )
        data[self.key] = user
        return await handler(event, data)
