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
from bot.filters.ad import IsCurseWordsFilter, IsLimitAdsPerDayFilter
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.handlers.user.ads.utils import ads_list
from bot.keyboards.inline.ad import get_ads_list_keyboard, AdListControlCallback, AdListActionCallback, \
    get_ad_actions_keyboard, AdActionCallback, get_ad_action_cancel_keyboard
from bot.keyboards.inline.menu import MenuItemCallback
from bot.loader import bot
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.schemas.ad import EditAdTextModel, UtilsAdModel, NewAdModel
from bot.states.ad import EditAdTextState, DuplicateAdTextState
from bot.utils.misc.ad import get_text_message_ad, get_text_error_action_ad, get_advertising_for_message, \
    get_advertising_from_string, get_text_when_ad_deleted, get_lengths, get_media_from_photo_ids, \
    send_channel_message_ad

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
    AdListActionCallback.filter(F.action == Action.select),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ads_list_select(
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
