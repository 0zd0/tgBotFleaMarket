import logging
import traceback
from typing import Any

import emoji
from aiogram import Router, F, flags
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery
from aiogram.utils.formatting import as_list, Text, TextLink, Italic

from bot.constants import LIMIT_ADS_ON_PAGE, LIMIT_LENGTH_IN_CAPTION
from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.enums.action import Action
from bot.enums.db.role import ALL
from bot.enums.menu import MainMenuItemCallback
from bot.filters.ad import IsCurseWordsFilter
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.keyboards.inline.ad import get_ads_list_keyboard, AdListControlCallback, AdListActionCallback, \
    get_ad_actions_keyboard, AdActionCallback, get_cancel_ad_action_keyboard
from bot.keyboards.inline.menu import MenuItemCallback
from bot.loader import bot
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.schemas.ad import EditAdTextModel, UtilsAdModel
from bot.states.ad import EditAdTextState
from bot.utils.misc.ad import get_text_message_ad, get_text_error_action_ad, get_advertising_for_message, \
    get_advertising_from_string, get_text_when_ad_deleted, get_lengths

router = Router()
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    any_state,
    MenuItemCallback.filter(F.item == MainMenuItemCallback.MY_ADS),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=3)
async def my_ads(
        call: CallbackQuery,
        state: FSMContext,
) -> Any:
    await state.clear()
    await ads_list(call)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    any_state,
    AdListActionCallback.filter(F.action == Action.toggle),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ads_list_toggle(
        call: CallbackQuery,
        callback_data: AdListActionCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    await ads_info(call, callback_data.ad_id, callback_data.page)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    any_state,
    AdListControlCallback.filter(F.action.in_({Action.prev, Action.next})),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ads_list_control(
        call: CallbackQuery,
        callback_data: AdListControlCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    await ads_list(call, callback_data.page)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    any_state,
    AdActionCallback.filter(F.action == Action.back),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ad_back(
        call: CallbackQuery,
        callback_data: AdActionCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    await ads_list(call, callback_data.page)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    any_state,
    AdActionCallback.filter(F.action == Action.delete),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ad_delete(
        call: CallbackQuery,
        callback_data: AdActionCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    try:
        await AdModel.ad_archive(callback_data.ad_id)
        ad = await AdModel.get_by_id(callback_data.ad_id)
        advertising = get_advertising_from_string(ad.text_advertising)
        old_text = get_text_message_ad(
                text=ad.text,
                entities=UtilsAdModel.get_entities_obj(ad.entities),
                from_user=call.from_user,
                bot_username=config.telegram.bot_username,
                advertising=get_advertising_for_message(advertising),
                from_user_name=ad.user_name,
            )
        new_text = as_list(
            get_text_when_ad_deleted(),
            old_text
        )
        await bot.edit_message_text(
            text=new_text.as_markdown(),
            chat_id=config.telegram.channel_id,
            message_id=ad.channel_message_id,
            disable_web_page_preview=True,
        )
    except TelegramBadRequest as e:
        await AdModel.ad_archive(callback_data.ad_id)
        error = as_list(
            Text('Сообщение не найдено в канале. Но оно в любому случае удалено')
        )
        await call.message.answer(text=error.as_markdown())
    except (Exception,) as e:
        logging.error('Ошибка при удалении объявления')
        traceback.print_exc()
    finally:
        await ads_list(call)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    StateFilter(EditAdTextState),
    AdActionCallback.filter(F.action == Action.cancel),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ad_edit_cancel(
        call: CallbackQuery,
        callback_data: AdActionCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    await ads_info(call, callback_data.ad_id, callback_data.page)


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    any_state,
    AdActionCallback.filter(F.action == Action.edit),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ad_edit_start(
        call: CallbackQuery,
        callback_data: AdActionCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    content = as_list(
        Text(f'Введите новый текст объявления:'),
    )
    cancel_message = await call.message.edit_text(
        text=content.as_markdown(),
        reply_markup=get_cancel_ad_action_keyboard(callback_data.ad_id, page=callback_data.page).as_markup()
    )
    await state.set_state(EditAdTextState.NEW_TEXT)
    await state.update_data(
        ad_id=callback_data.ad_id,
        cancel_message_chat_id=cancel_message.chat.id,
        cancel_message_id=cancel_message.message_id,
        page=callback_data.page,
    )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    EditAdTextState.NEW_TEXT,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsCurseWordsFilter(config.curse_words.file_path),
)
@flags.rate_limit(limit=3)
async def ad_edit_text(
        message: Message,
        state: FSMContext
) -> Any:
    data = EditAdTextModel(**(await state.get_data()))
    ad = await AdModel.get_by_id(data.ad_id)
    text = message.text
    ad_text_length, text_additional_to_ad_length = await get_lengths(text, message.from_user,
                                                                     config.telegram.bot_username,
                                                                     advertising_text=ad.text_advertising)
    if text_additional_to_ad_length + ad_text_length > LIMIT_LENGTH_IN_CAPTION:
        limit_ad_text = LIMIT_LENGTH_IN_CAPTION - text_additional_to_ad_length
        error = as_list(
            Text(Text(f'{emoji.emojize(":cross_mark:")} Вы превысили лимит символов. '),
                 Italic(f'({ad_text_length}/{limit_ad_text})')),
            Text(),
            Text('Напишите текст покороче:'),
        )
        return await message.answer(text=error.as_markdown())
    entities_json = UtilsAdModel.get_entities_json(message.entities) if message.entities else []
    advertising = get_advertising_from_string(ad.text_advertising)
    new_text = get_text_message_ad(
        text=text,
        entities=message.entities or [],
        from_user=message.from_user,
        bot_username=config.telegram.bot_username,
        advertising=get_advertising_for_message(advertising)
    )
    try:
        await bot.edit_message_text(
            text=new_text.as_markdown(),
            chat_id=config.telegram.channel_id,
            message_id=ad.channel_message_id,
            disable_web_page_preview=True
        )
    except TelegramBadRequest as e:
        if 'specified new message content and reply markup are exactly the same as a current content' in e.message:
            error = as_list(
                Text('Сообщение с точно таким же текстом')
            )
            await message.answer(text=error.as_markdown())
        else:
            error = as_list(
                Text('Сообщение не найдено в канале. Поэтому оно автоматически удалено')
            )
            await AdModel.ad_archive(data.ad_id)
            await message.answer(text=error.as_markdown())
            await ads_list(message)
            await state.clear()
    except (Exception,) as e:
        logging.error('Ошибка при редактировании сообщения')
        traceback.print_exc()
        error = get_text_error_action_ad()
        await message.answer(text=error.as_markdown())
    else:
        await AdModel.edit_text(
            ad_id=data.ad_id, text=text, entities=entities_json
        )
        await message.answer(
            text=Text(f'Текст отредактирован').as_markdown(),
        )
        await ads_info(message, data.ad_id, data.page)
        await state.clear()
    finally:
        await bot.delete_message(
            chat_id=data.cancel_message_chat_id,
            message_id=data.cancel_message_id
        )


async def ads_info(
        message: Message | CallbackQuery,
        ad_id: int,
        page: int = 0
) -> None:
    ad = await AdModel.get_by_id(ad_id)
    ad_text = Text.from_entities(ad.text, UtilsAdModel.get_entities_obj(ad.entities))
    content = as_list(
        TextLink(f'Объявление:',
                 url=f'https://t.me/c/{str(config.telegram.channel_id).replace("-100", "")}/{ad.channel_message_id}'),
        Text(),
        ad_text,
    )
    if isinstance(message, CallbackQuery):
        call = message
        await call.message.edit_text(
            text=content.as_markdown(),
            reply_markup=get_ad_actions_keyboard(ad, page).as_markup()
        )
    else:
        await message.answer(
            text=content.as_markdown(),
            reply_markup=get_ad_actions_keyboard(ad, page).as_markup()
        )


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
