from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.enums.action import Action
from bot.enums.menu import Cancel


class MiscActionCallback(CallbackData, prefix='misc'):
    action: Action


inline_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=Cancel.CANCEL.value,
                callback_data=MiscActionCallback(action=Action.cancel).pack()
            )
        ]
    ]
)
