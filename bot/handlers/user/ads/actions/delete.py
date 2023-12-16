import logging
import traceback
from typing import Any, Text

from aiogram import Router, F, flags
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery
from aiogram.utils.formatting import as_list

from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.enums.action import Action
from bot.enums.db.role import ALL
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.handlers.user.ads.utils import ads_list
from bot.keyboards.inline.ad import AdActionCallback
from bot.loader import bot
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.schemas.ad import UtilsAdModel
from bot.utils.misc.ad import get_advertising_from_string, get_text_message_ad, get_advertising_for_message, \
    get_text_when_ad_deleted

router = Router()
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


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
        if ad.photo_ids:
            await bot.edit_message_caption(
                caption=new_text.as_markdown(),
                chat_id=config.telegram.channel_id,
                message_id=ad.channel_message_id,
            )
        else:
            await bot.edit_message_text(
                text=new_text.as_markdown(),
                chat_id=config.telegram.channel_id,
                message_id=ad.channel_message_id,
                disable_web_page_preview=True,
            )
    except TelegramBadRequest as e:
        traceback.print_exc()
        if 'MESSAGE_ID_INVALID' in e.message:
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
