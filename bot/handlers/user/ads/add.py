import logging
import traceback
from typing import Any, List

import emoji
from aiogram import Router, F, flags
from aiogram.enums import ChatType, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, InputMediaPhoto, CallbackQuery
from aiogram.utils.formatting import as_list, Text, Bold, Italic

from bot.custom_types.album import Album
from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.db.user.model import UserModel
from bot.enums.action import Action
from bot.enums.db.role import ALL
from bot.enums.menu import Cancel, MainMenu
from bot.filters.ad import IsCurseWordsFilter, IsLimitLengthAdFilter, IsLimitAdsPerDayFilter
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.keyboards.default.menu import menu_keyboards
from bot.keyboards.default.misc import cancel
from bot.keyboards.inline.ad import new_ad_skip_images_keyboard, new_ad_public_images_keyboard, NewAdCallback
from bot.loader import bot
from bot.middlewares import AlbumMiddleware
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.schemas.ad import NewAdModel, UtilsAdModel
from bot.states.ad import NewAdState
from bot.utils.misc.ad import get_text_error_action_ad, get_text_message_ad, get_advertising_for_message

EMOJI_TO_BUTTON = emoji.emojize(":backhand_index_pointing_down:")

router = Router()
router.message.outer_middleware(AlbumMiddleware())
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text == Cancel.CANCEL,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=3)
async def new_ad_cancel(message: Message, state: FSMContext, user: UserModel):
    await state.clear()
    content = as_list(
        Text(f'{emoji.emojize(":cross_mark:")} Отмена создания объявления')
    )
    await message.answer(text=content.as_markdown(), reply_markup=menu_keyboards.get(user.role))


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text == MainMenu.NEW_AD,
    any_state,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=3)
async def new_ad_start(
        message: Message,
        state: FSMContext,
) -> Any:
    await state.clear()
    await state.set_state(NewAdState.TEXT)
    content = as_list(
        Text(Text(f'Пожалуйста, отправьте боту Ваш текст объявления.'), ),
        Text(),
        Text('Не забудьте указать номер телефона, это поможет потенциальным клиентам быстрее с Вами связаться!'),
    )
    await message.answer(
        text=content.as_markdown(),
        reply_markup=cancel
    )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.media_group_id,
    F.content_type.in_([ContentType.PHOTO]),
    NewAdState.TEXT,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=None)
async def new_ad_text_and_photos(
        message: Message,
        state: FSMContext,
        album: Album
) -> Any:
    first_message = album.messages[0]
    entities_raw = first_message.caption_entities or []
    entities = UtilsAdModel.get_entities_json(first_message.caption_entities)
    caption = first_message.caption
    if not caption:
        first_non_empty = next((s for s in album.captions if s), None)
        if first_non_empty:
            caption = first_non_empty
        else:
            return
    if await IsCurseWordsFilter(config.curse_words.file_path).check(message, caption, entities_raw):
        return
    if await IsLimitLengthAdFilter(config.telegram.max_length_ads).check(message, caption):
        return
    photo_ids = [photo.file_id for photo in album.photo]
    await message_text_and_photo(message, photo_ids)
    await state.update_data(photo_ids=photo_ids, text=caption, entities=entities)
    await state.set_state(NewAdState.MEDIA)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.caption,
    F.content_type.in_([ContentType.PHOTO]),
    NewAdState.TEXT,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=None)
async def new_ad_text_and_photo(
        message: Message,
        state: FSMContext,
) -> Any:
    entities = UtilsAdModel.get_entities_json(message.caption_entities)
    caption = message.caption
    if await IsCurseWordsFilter(config.curse_words.file_path).check(message, caption, message.caption_entities or []):
        return
    if await IsLimitLengthAdFilter(config.telegram.max_length_ads).check(message, caption):
        return
    photo = message.photo.pop()
    photo_ids = [photo.file_id]
    await message_text_and_photo(message, photo_ids)
    await state.update_data(
        photo_ids=photo_ids,
        text=caption,
        entities=entities
    )
    await state.set_state(NewAdState.MEDIA)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    NewAdState.TEXT,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
    ~IsCurseWordsFilter(config.curse_words.file_path),
    ~IsLimitLengthAdFilter(config.telegram.max_length_ads),
)
async def new_ad_text(
        message: Message,
        state: FSMContext,
) -> Any:
    text = message.text
    entities = UtilsAdModel.get_entities_json(message.entities)
    content = as_list(
        Text(Bold(f'Отправьте фото для объявления.'), Italic(' (максимум 10 шт.)')),
        Text(),
        Text(Text(f'Если объявление без фото, то нажмите'), Bold(f' ПРОПУСТИТЬ '),
             Text(f'{EMOJI_TO_BUTTON}')),
    )
    await message.answer(
        text=content.as_markdown(),
        reply_markup=new_ad_skip_images_keyboard
    )
    await state.update_data(text=text, entities=entities)
    await state.set_state(NewAdState.MEDIA)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.media_group_id,
    F.content_type.in_([ContentType.PHOTO]),
    NewAdState.MEDIA,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=None)
async def new_ad_photos(
        message: Message,
        state: FSMContext,
        album: Album
) -> Any:
    photo_ids = [photo.file_id for photo in album.photo]
    await handle_add_media(message, state, photo_ids)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_([ContentType.PHOTO]),
    NewAdState.MEDIA,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=None)
async def new_ad_photo(
        message: Message,
        state: FSMContext,
) -> Any:
    photo = message.photo.pop()
    photo_ids = [photo.file_id]
    await handle_add_media(message, state, photo_ids)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    NewAdState.MEDIA,
    NewAdCallback.filter(F.action.in_({Action.skip, Action.public})),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=5)
async def new_ad_callback_end(
        call: CallbackQuery,
        state: FSMContext,
        user: UserModel,
) -> Any:
    data = NewAdModel(**(await state.get_data()))
    ads_limit_must = config.telegram.advertising_every_ad - 1
    ads = await AdModel.get_last(limit=ads_limit_must)
    advertising = [
        Text(line) for line in config.telegram.advertising.split('\n')
    ] if len(ads) == ads_limit_must and all(ad.text_advertising is None for ad in ads) else []
    if advertising:
        advertising = get_advertising_for_message(advertising)
        data.text_advertising = config.telegram.advertising
    text = get_text_message_ad(
        text=data.text,
        entities=data.entities or [],
        from_user=call.from_user,
        bot=(await bot.get_me()),
        advertising=advertising
    )
    media = [InputMediaPhoto(media=photo_id) for photo_id in data.photo_ids or []]
    try:
        if media:
            send_photos = await bot.send_media_group(
                chat_id=config.telegram.channel_id,
                media=media,
            )
            send_message = await bot.send_message(
                chat_id=config.telegram.channel_id,
                reply_to_message_id=send_photos[0].message_id,
                text=text.as_markdown(),
                entities=data.entities,
                disable_web_page_preview=True
            )
        else:
            send_message = await bot.send_message(
                chat_id=config.telegram.channel_id,
                text=text.as_markdown(),
                entities=data.entities,
                disable_web_page_preview=True
            )
    except (Exception,):
        logging.error('Ошибка при отправке объявления в канал')
        traceback.print_exc()
        content = get_text_error_action_ad()
        await call.message.answer(text=content.as_markdown(), reply_markup=menu_keyboards.get(user.role))
    else:
        data.channel_message_id = send_message.message_id
        await AdModel.create_ad(
            call.from_user.id,
            data
        )
        content = as_list(
            Text(f'Ваше объявление успешно размещено!')
        )
        await call.message.answer(text=content.as_markdown(), reply_markup=menu_keyboards.get(user.role))
    finally:
        await call.answer()
        await state.clear()


async def message_text_and_photo(
        message: Message,
        photo_ids: List[str]
) -> None:
    text_public = [
        Text(Text(f'Если все правильно, то нажмите кнопку'), Bold(' ОПУБЛИКОВАТЬ '), Text(f'{EMOJI_TO_BUTTON}'))
    ]
    if len(photo_ids) < 10:
        text_public = [
            Text('Вы можете отправить еще фото.'),
            Text(Text(f'Если фото больше нет, то нажмите кнопку'), Bold(' ОПУБЛИКОВАТЬ '),
                 Text(f'{EMOJI_TO_BUTTON}')),
        ]
    content = as_list(
        Text(Bold(f'Фотографии успешно загружены!'), Italic(f' ({len(photo_ids)}/10)')),
        Text(),
        *text_public
    )
    await message.answer(
        text=content.as_markdown(),
        reply_markup=new_ad_public_images_keyboard
    )


async def message_max_medias(
        message: Message,
        count_total_photo_ids: int
) -> None:
    content = as_list(
        Text(Bold(f'Вы отправили файлов больше, чем можно добавить.'),
             Italic(f' ({count_total_photo_ids}/10)')),
    )
    await message.answer(
        text=content.as_markdown(),
        reply_markup=new_ad_public_images_keyboard
    )


async def handle_add_media(
        message: Message,
        state: FSMContext,
        photo_ids: List[str]
) -> None:
    data = NewAdModel(**(await state.get_data()))
    count_total_photo_ids = len(photo_ids) + (len(data.photo_ids) if data.photo_ids else 0)
    if data.photo_ids and count_total_photo_ids > 10:
        return await message_max_medias(message, count_total_photo_ids)
    if data.photo_ids:
        photo_ids.extend(data.photo_ids)
    await state.update_data(photo_ids=photo_ids)
    await message_text_and_photo(message, photo_ids)
