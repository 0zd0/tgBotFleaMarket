from typing import Any

import emoji
from aiogram import Router, F, flags
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import as_list, Text, Italic

from bot.constants import LIMIT_LENGTH_IN_CAPTION
from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.enums.action import Action
from bot.enums.db.role import ALL
from bot.filters.ad import IsLimitAdsPerDayFilter, IsCurseWordsFilter
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.handlers.user.ads.my_ads import ads_info
from bot.handlers.user.ads.utils import duplicate_ad
from bot.keyboards.inline.ad import AdActionCallback, get_ad_action_cancel_keyboard
from bot.loader import bot
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.schemas.ad import DuplicateAdModel, UtilsAdModel
from bot.states.ad import DuplicateAdTextState
from bot.utils.misc.ad import get_lengths

router = Router()
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    StateFilter(DuplicateAdTextState),
    AdActionCallback.filter(F.action == Action.cancel),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
)
@flags.rate_limit(limit=1)
async def ad_duplicate_cancel(
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
    AdActionCallback.filter(F.action == Action.duplicate),
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsLimitAdsPerDayFilter(config.telegram.max_ads_per_day),
)
@flags.rate_limit(limit=3)
async def ad_duplicate_start(
        call: CallbackQuery,
        callback_data: AdActionCallback,
        state: FSMContext,
) -> Any:
    await state.clear()
    await call.answer()
    ad = await AdModel.get_by_id(callback_data.ad_id)
    ad_text_length, text_additional_to_ad_length = await get_lengths(
        ad.text,
        call.from_user,
        config.telegram.bot_username,
        advertising_text=ad.text_advertising or config.telegram.advertising,
    )
    limit_ad_text = LIMIT_LENGTH_IN_CAPTION - text_additional_to_ad_length
    if text_additional_to_ad_length + ad_text_length > LIMIT_LENGTH_IN_CAPTION:
        content = as_list(
            Text(f'Текст прошлого объявления превышает текущий лимит символов. ',
                 Italic(f'({ad_text_length}/{limit_ad_text})')),
            Text(),
            Text('Введите новый текст(изображения продублируются, если они есть):'),
        )
        cancel_message = await call.message.answer(
            text=content.as_markdown(),
            reply_markup=get_ad_action_cancel_keyboard(callback_data.ad_id, page=callback_data.page).as_markup()
        )
        await state.set_state(DuplicateAdTextState.NEW_TEXT)
        await state.update_data(
            ad_id=callback_data.ad_id,
            cancel_message_chat_id=cancel_message.chat.id,
            cancel_message_id=cancel_message.message_id,
        )
    else:
        await duplicate_ad(
            call,
            ad,
            bot,
        )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    DuplicateAdTextState.NEW_TEXT,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter(),
    ~IsCurseWordsFilter(config.curse_words.file_path),
)
@flags.rate_limit(limit=3)
async def ad_duplicate_text(
        message: Message,
        state: FSMContext
) -> Any:
    data = DuplicateAdModel(**(await state.get_data()))
    ad = await AdModel.get_by_id(data.ad_id)
    text = message.text
    ad_text_length, text_additional_to_ad_length = await get_lengths(
        text,
        message.from_user,
        config.telegram.bot_username,
    )
    if text_additional_to_ad_length + ad_text_length > LIMIT_LENGTH_IN_CAPTION:
        limit_ad_text = LIMIT_LENGTH_IN_CAPTION - text_additional_to_ad_length
        error = as_list(
            Text(Text(f'{emoji.emojize(":cross_mark:")} Вы превысили лимит символов. '),
                 Italic(f'({ad_text_length}/{limit_ad_text})')),
            Text(),
            Text('Напишите текст покороче:'),
        )
        return await message.answer(text=error.as_markdown())
    ad.text = text
    ad.entities = UtilsAdModel.get_entities_json(message.entities)
    await duplicate_ad(
        message,
        ad,
        bot,
    )
    await state.clear()
