from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.enums.menu import MainMenuItemCallback, MainMenu


class MenuItemCallback(CallbackData, prefix='menu'):
    item: MainMenuItemCallback


inline_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MainMenu.NEW_AD.value,
                callback_data=MenuItemCallback(item=MainMenuItemCallback.NEW_AD).pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text=MainMenu.MY_ADS.value,
                callback_data=MenuItemCallback(item=MainMenuItemCallback.MY_ADS).pack()
            ),
        ],
    ]
)
