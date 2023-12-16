from typing import Callable, Any, Dict, Optional, Awaitable

import emoji
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.formatting import as_list, Text, Italic

from bot.constants import LIMIT_LENGTH_IN_CAPTION
from bot.custom_types.album import Album
from bot.data.main_config import config
from bot.enums.menu import Cancel
from bot.schemas.ad import NewAdModel
from bot.states.ad import NewAdState
from bot.utils.misc.ad import get_lengths
from bot.utils.misc.menu import send_main_menu


class CheckAdLimitLengthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Optional[Any]:
        state: Optional[FSMContext] = data.get("state", None)
        album: Optional[Album] = data.get("album", None)
        message_text = event.text or event.caption if isinstance(event, Message) else None
        if state and message_text not in (
            Cancel.CANCEL,
        ):
            key = await state.get_state()
            state_data = NewAdModel(**(await state.get_data()))
            if key == NewAdState.TEXT and isinstance(event, Message):
                ad_text = message_text
                if album:
                    ad_text, _ = album.get_caption_and_entities()
            else:
                ad_text = state_data.text

            ad_text_length, text_additional_to_ad_length = await get_lengths(ad_text, event.from_user,
                                                                             config.telegram.bot_username)
            limit_ad_text = LIMIT_LENGTH_IN_CAPTION - text_additional_to_ad_length
            if text_additional_to_ad_length + ad_text_length > LIMIT_LENGTH_IN_CAPTION:
                smile_before_error = emoji.emojize(':cross_mark:')
                if key == NewAdState.TEXT:
                    content = as_list(
                        Text(Text(f'{smile_before_error} Вы превысили лимит символов. '),
                             Italic(f'({ad_text_length}/{limit_ad_text})')),
                        Text(),
                        Text('Напишите текст покороче:'),
                    )
                    return await event.answer(
                        text=content.as_markdown(),
                    )
                elif key in (
                    NewAdState.MEDIA,
                ):
                    await state.clear()
                    content = as_list(
                        Text(Text(f'{smile_before_error} У вас превышен лимит символов в тексте объявления. '),
                             Italic(f'({ad_text_length}/{limit_ad_text})')),
                        Text(),
                        Text('Начните заполнять заново'),
                    )

                    if isinstance(event, Message):
                        await event.answer(
                            text=content.as_markdown(),
                            reply_markup=ReplyKeyboardRemove(),
                        )
                        return await send_main_menu(event, event.from_user)
                    elif isinstance(event, CallbackQuery):
                        await event.answer()
                        await event.message.answer(
                            text=content.as_markdown(),
                            reply_markup=ReplyKeyboardRemove(),
                        )
                        return await send_main_menu(event.message, event.from_user)
        return await handler(event, data)
