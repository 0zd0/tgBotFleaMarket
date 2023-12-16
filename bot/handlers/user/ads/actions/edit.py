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
from aiogram.utils.formatting import as_list, Text, Italic

from bot.constants import LIMIT_LENGTH_IN_CAPTION
from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.enums.action import Action
from bot.enums.db.role import ALL
from bot.filters.ad import IsCurseWordsFilter
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.handlers.user.ads.my_ads import ads_info
from bot.handlers.user.ads.utils import ads_list
from bot.keyboards.inline.ad import get_ad_action_cancel_keyboard, AdActionCallback
from bot.loader import bot
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.schemas.ad import EditAdTextModel, UtilsAdModel
from bot.states.ad import EditAdTextState
from bot.utils.misc.ad import get_lengths, get_advertising_from_string, get_text_message_ad, \
    get_advertising_for_message, get_text_error_action_ad

router = Router()
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


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
        reply_markup=get_ad_action_cancel_keyboard(callback_data.ad_id, page=callback_data.page).as_markup()
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
@flags.rate_limit(limit=1)
async def ad_edit_text(
        message: Message,
        state: FSMContext
) -> Any:
    data = EditAdTextModel(**(await state.get_data()))
    ad = await AdModel.get_by_id(data.ad_id)
    text = message.text
    ad_text_length, text_additional_to_ad_length = await get_lengths(
        text,
        message.from_user,
        config.telegram.bot_username,
        advertising_text=ad.text_advertising or config.telegram.advertising
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
    advertising = get_advertising_from_string(ad.text_advertising)
    new_text = get_text_message_ad(
        text=text,
        entities=message.entities or [],
        from_user=message.from_user,
        bot_username=config.telegram.bot_username,
        advertising=get_advertising_for_message(advertising)
    )
    try:
        if ad.photo_ids:
            await bot.edit_message_caption(
                caption=new_text.as_markdown(),
                chat_id=config.telegram.channel_id,
                message_id=ad.channel_message_id
            )
        else:
            await bot.edit_message_text(
                text=new_text.as_markdown(),
                chat_id=config.telegram.channel_id,
                message_id=ad.channel_message_id,
                disable_web_page_preview=True
            )
    except TelegramBadRequest as e:
        traceback.print_exc()
        if 'specified new message content and reply markup are exactly the same as a current content' in e.message:
            error = as_list(
                Text('Сообщение с точно таким же текстом')
            )
            await message.answer(text=error.as_markdown())
        elif 'MESSAGE_ID_INVALID' in e.message:
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
            ad_id=data.ad_id, text=text, entities=message.entities, user_name=message.from_user.full_name
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
