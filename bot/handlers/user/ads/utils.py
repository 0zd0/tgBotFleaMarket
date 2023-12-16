from typing import List, Optional

import emoji
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, MessageEntity
from aiogram.utils.formatting import as_list, Text, Italic

from bot.constants import LIMIT_ADS_ON_PAGE, LIMIT_LENGTH_IN_CAPTION
from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.keyboards.inline.ad import get_ads_list_keyboard
from bot.schemas.ad import UtilsAdModel, NewAdModel
from bot.utils.misc.ad import get_lengths, get_advertising_from_string, get_advertising_for_message, \
    get_text_message_ad, get_media_from_photo_ids, send_channel_message_ad


async def ads_list(
        message: Message | CallbackQuery,
        page: int = 0
) -> None:
    offset = max(LIMIT_ADS_ON_PAGE * page, 0)
    ads = await AdModel().get_all_ads_by_user(user_id=message.from_user.id, offset=offset)
    count_ads = await AdModel().get_count_all_ads_by_user(user_id=message.from_user.id)
    content = as_list(
        Text(f'Объявлений {count_ads} шт.'),
    )
    if isinstance(message, Message):
        await message.answer(
            text=content.as_markdown(),
            reply_markup=get_ads_list_keyboard(ads, count_ads, page, offset).as_markup()
        )
    else:
        call = message
        await call.message.edit_text(
            text=content.as_markdown(),
            reply_markup=get_ads_list_keyboard(ads, count_ads, page, offset).as_markup()
        )


async def duplicate_ad(
        message: Message | CallbackQuery,
        ad: AdModel,
        bot: Bot,
) -> None:
    ads_limit_must = config.telegram.advertising_every_ad - 1
    ads = await AdModel.get_last(limit=ads_limit_must)
    advertising = get_advertising_from_string(config.telegram.advertising) \
        if len(ads) == ads_limit_must and all(ad.text_advertising is None for ad in ads) \
        else None
    advertising_text = None
    if advertising:
        advertising = get_advertising_for_message(advertising)
        advertising_text = config.telegram.advertising
    text = get_text_message_ad(
        text=ad.text,
        entities=UtilsAdModel.get_entities_obj(ad.entities) or [],
        from_user=message.from_user,
        bot_username=config.telegram.bot_username,
        advertising=advertising
    )
    media = await get_media_from_photo_ids(
        photo_ids=ad.photo_ids,
        text=text,
    )
    send_message = await send_channel_message_ad(
        media,
        bot,
        text,
    )
    await AdModel.create_ad(
        user_id=ad.user_id,
        data=NewAdModel(
            text=ad.text,
            entities=UtilsAdModel.get_entities_obj(ad.entities),
            photo_ids=ad.photo_ids,
            channel_message_id=send_message.message_id,
            text_advertising=advertising_text,
            user_name=ad.user_name or message.from_user.full_name,
        )
    )
    content = as_list(
        Text(f'Продублировано'),
    )
    if isinstance(message, Message):
        await message.answer(
            text=content.as_markdown(),
        )
    else:
        call = message
        await call.message.answer(
            text=content.as_markdown(),
        )
