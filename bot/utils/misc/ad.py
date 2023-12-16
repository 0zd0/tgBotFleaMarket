from typing import List, Optional

import emoji
from aiogram import Bot
from aiogram.types import MessageEntity, User, InputMediaPhoto
from aiogram.utils.formatting import as_list, Text, Italic

from bot.data.main_config import config
from bot.utils.misc.mention import get_mention


def get_additional_text_for_ad(
        from_user: User,
        bot_username: str,
        from_user_name: Optional[str] = None
) -> Text:
    return as_list(
        Text(),
        Text(
            Text(f'Отправлено пользователем: '), get_mention(
                from_user,
                from_user_name if from_user_name
                else from_user.full_name
            )
        ),
        Text(),
        Text(),
        Text('___________________'),
        Text('Чтобы опубликовать объявление, нажмите'),
        Text(f'{emoji.emojize(":backhand_index_pointing_right:")}{emoji.emojize(":backhand_index_pointing_right:")}'
             f'@{bot_username}'
             f'{emoji.emojize(":backhand_index_pointing_left:")}{emoji.emojize(":backhand_index_pointing_left:")}'),
    )


def get_text_message_ad(
        text: str,
        entities: List[MessageEntity],
        from_user: User,
        bot_username: str,
        advertising: Optional[Text],
        from_user_name: Optional[str] = None
) -> Text:
    text = as_list(
        Text.from_entities(text, entities),
        get_additional_text_for_ad(from_user, bot_username, from_user_name),
    )
    if advertising is not None:
        text = as_list(
            text,
            advertising
        )

    return text


def get_advertising_from_string(
        text: Optional[str]
) -> Optional[Text]:
    if not text:
        return None
    texts = [
        Text(line) for line in text.split('\n')
    ]
    return as_list(
        *texts
    ) if text else None


def get_advertising_for_message(
        advertising: Optional[Text]
) -> Optional[Text]:
    if not advertising:
        return None
    return as_list(
        Text(),
        Text('___________________'),
        Text(),
        Text('Реклама:'),
        Text(),
        advertising
    )


def get_text_when_ad_deleted() -> Text:
    return as_list(
        Text(Italic(f'{emoji.emojize(":cross_mark:")} Неактуально')),
        Text(),
    )


def get_text_error_action_ad(
) -> Text:
    return as_list(
        Text(f'Произошла ошибка, обратитесь к @{config.telegram.support_username} или попробуйте позже')
    )


def get_length_text(
        text: str
) -> int:
    return len(text.encode('utf-16-le')) // 2


async def get_lengths(
        ad_text: str,
        from_user: User,
        bot_username: str,
        advertising_text: str = config.telegram.advertising,
        from_user_name: Optional[str] = None
) -> tuple[int, int]:
    advertising = get_advertising_for_message(get_advertising_from_string(advertising_text))
    text_deleted = get_text_when_ad_deleted()
    text_additional = get_additional_text_for_ad(
        from_user,
        bot_username,
        from_user_name
    )
    full_text_additional_to_ad = as_list(
        text_deleted,
        text_additional,
        advertising,
    )
    text_additional_to_ad, _ = full_text_additional_to_ad.render()
    ad_text_length = get_length_text(ad_text)
    text_additional_to_ad_length = get_length_text(text_additional_to_ad)
    return ad_text_length, text_additional_to_ad_length


async def get_media_from_photo_ids(
        photo_ids: List[str],
        # entities: List[MessageEntity],
        text: Text,
) -> List[InputMediaPhoto]:
    media = []
    if photo_ids:
        for index, photo_id in enumerate(photo_ids):
            if index == 0:
                media.append(InputMediaPhoto(
                    media=photo_id,
                    caption=text.as_markdown(),
                    # caption_entities=entities,
                ))
            else:
                media.append(InputMediaPhoto(
                    media=photo_id,
                ))
    return media


async def send_channel_message_ad(
        media: Optional[List[InputMediaPhoto]],
        bot: Bot,
        text: Text,
):
    if media:
        send_messages = await bot.send_media_group(
            chat_id=config.telegram.channel_id,
            media=media,
        )
        send_message = send_messages[0]
    else:
        send_message = await bot.send_message(
            chat_id=config.telegram.channel_id,
            text=text.as_markdown(),
            disable_web_page_preview=True
        )
    return send_message
