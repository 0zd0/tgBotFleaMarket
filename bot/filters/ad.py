import re
from typing import Union, Dict, Any, List

from aiogram import Bot
from aiogram.enums import MessageEntityType
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User, MessageEntity
from aiogram.utils.formatting import Text, as_list, Italic

from bot.constants import REGEX_LINKS
from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.db.user.model import UserModel
from bot.keyboards.default.menu import menu_keyboards
from bot.utils.misc.curse_words import get_curse_words


class IsLimitAdsPerDayFilter(Filter):
    def __init__(self, limit: int):
        self.limit = limit

    async def __call__(
        self,
        message: Message,
        state: FSMContext,
        event_from_user: User,
        bot: Bot,
        user: UserModel,
    ) -> Union[bool, Dict[str, Any]]:
        return await self.check(message, user, state)

    async def check(
            self,
            message: Message,
            user: UserModel,
            state: FSMContext,
    ) -> bool:
        ads = await AdModel.get_ads_day_by_user(message.from_user.id)
        if max(self.limit - len(ads), 0) == 0:
            await state.clear()
            content = as_list(
                Text(Text(f'Вы уже достигли лимита объявлений на сегодня. '), Italic(f'(Максимум {self.limit})')),
            )
            await message.answer(
                text=content.as_markdown(),
                reply_markup=menu_keyboards.get(user.role),
            )
            return True
        return False


class IsCurseWordsFilter(Filter):
    def __init__(self, file_path: str):
        self.file_path = file_path

    async def __call__(
        self,
        message: Message,
        event_from_user: User,
        bot: Bot,
        user: UserModel,
    ) -> Union[bool, Dict[str, Any]]:
        text = message.text or message.caption or ""
        entities = message.entities or message.caption_entities or []
        return await self.check(message, text, entities)

    async def check(
            self,
            message: Message,
            text: str,
            entities: List[MessageEntity]
    ) -> bool:
        curse_words = await get_curse_words(self.file_path)
        if any(word in text.lower() for word in curse_words):
            await message.reply(
                text=Text('Ваш текст содержит запрещенные слова, отправьте текст без запрещенных слов.').as_markdown()
            )
            return True
        urls = re.findall(REGEX_LINKS, text.lower())
        if urls or any(entity.type in (MessageEntityType.URL, MessageEntityType.TEXT_LINK) for entity in entities):
            await message.reply(
                text=as_list(
                    Text(f'Ссылки в тексте объявления запрещены. Если хотите прорекламировать что-то, свяжитесь '
                         f'с администратором @{config.telegram.support_username}'),
                    Text(),
                    Text(f'Отправьте текст объявления без ссылок:'),
                ).as_markdown()
            )
            return True
        return False
