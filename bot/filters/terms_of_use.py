from typing import Union, Dict, Any

from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message, User

from bot.db.user.model import UserModel


class IsAcceptTermsOfUseFilter(Filter):

    async def __call__(
        self,
        message: Message,
        event_from_user: User,
        bot: Bot,
        user: UserModel,
    ) -> Union[bool, Dict[str, Any]]:
        return user.terms_of_use
