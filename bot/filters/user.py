from typing import Any, Union, Dict, List

from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message, User

from bot.db.user.model import UserModel
from bot.enums.db.role import Role


class RoleFilter(Filter):
    def __init__(self, roles: List[Role]):
        self.roles = roles

    async def __call__(
        self,
        message: Message,
        event_from_user: User,
        bot: Bot,
        user: UserModel,
    ) -> Union[bool, Dict[str, Any]]:
        if user.role not in self.roles:
            return False

        return True
