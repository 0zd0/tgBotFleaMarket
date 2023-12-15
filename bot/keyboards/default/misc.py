from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.enums.menu import Cancel


cancel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=Cancel.CANCEL.value),
        ],
    ],
    resize_keyboard=True
)
