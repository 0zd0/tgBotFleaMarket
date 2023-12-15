from typing import Union

from aiogram.types import User
from aiogram.utils.formatting import TextLink, TextMention


def get_mention(user: User, text_link: str | None = None) -> Union[TextLink, TextMention]:
    if not text_link:
        text_link = user.full_name
    if user.username:
        return TextLink(text_link, url=f't.me/{user.username}')
    else:
        return TextMention(text_link, user=user)
