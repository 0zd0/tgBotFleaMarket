from typing import List

import emoji
from aiogram.types import MessageEntity, User
from aiogram.utils.formatting import as_list, Text

from bot.data.main_config import config
from bot.utils.misc.mention import get_mention


def get_text_message_ad(
        text: str,
        entities: List[MessageEntity],
        from_user: User,
        bot: User,
        advertising: List[Text]
) -> Text:
    text = as_list(
        Text.from_entities(text, entities),
        Text(),
        Text(Text(f'Отправлено пользователем: '), get_mention(from_user)),
        Text(),
        Text(),
        Text('___________________'),
        Text('Чтобы опубликовать объявление, нажмите'),
        Text(f'{emoji.emojize(":backhand_index_pointing_right:")}{emoji.emojize(":backhand_index_pointing_right:")}'
             f'@{bot.username}'
             f'{emoji.emojize(":backhand_index_pointing_left:")}{emoji.emojize(":backhand_index_pointing_left:")}'),
        *advertising
    )

    return text


def get_advertising_for_message(
        advertising: List[Text]
) -> List[Text]:
    return [
        Text(),
        Text('___________________'),
        Text(),
        Text('Реклама:'),
        Text(),
        *advertising
    ]


def get_text_error_action_ad(
) -> Text:
    return as_list(
        Text(f'Произошла ошибка, обратитесь к @{config.telegram.support_username} или попробуйте позже')
    )
