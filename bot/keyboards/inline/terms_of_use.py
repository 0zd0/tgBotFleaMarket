from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.enums.action import Action
from bot.enums.menu import Buttons


class TermsOfUseCallback(CallbackData, prefix='terms'):
    action: Action


accept_terms_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=Buttons.ACCEPT_TERMS.value,
                callback_data=TermsOfUseCallback(action=Action.accept).pack()
            )
        ]
    ]
)
