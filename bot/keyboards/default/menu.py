from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.enums.menu import MainMenu
from bot.enums.db.role import Role

main_menu_default = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=MainMenu.MENU.value),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder=MainMenu.SELECT_ACTION.value
)

menu_keyboards = {
    Role.SUPER_ADMIN: main_menu_default,
    Role.USER: main_menu_default,
    Role.MANAGER: main_menu_default,
    Role.ADMIN: main_menu_default,
}
