import logging
from typing import Optional, Union

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply


async def notify(
        bot: Bot,
        user_ids: list,
        text: str,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
):
    if not user_ids:
        return
    for user_id in user_ids:
        try:
            await bot.send_message(
                user_id,
                text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview)
        except Exception as e:
            logging.exception(e)


async def on_startup_notify(bot: Bot, user_ids: list) -> None:
    await notify(bot, user_ids, 'Bot is running')
