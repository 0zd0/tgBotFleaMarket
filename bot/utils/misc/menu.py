from aiogram.types import Message, CallbackQuery
from aiogram.utils.formatting import as_list, Text

from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.keyboards.inline.menu import inline_menu
from bot.loader import bot


async def send_main_menu(
    message: Message | CallbackQuery,
    welcome: bool = False,
):
    chat = await bot.get_chat(config.telegram.channel_id)
    ads = await AdModel.get_ads_day_by_user(message.from_user.id)
    content = as_list(
        Text(f'Кол-во объявлений на сегодня {max(config.telegram.max_ads_per_day - len(ads), 0)} шт.'),
        Text(f''),
        Text(f'Связь с администратором @{config.telegram.support_username}'),
        Text(f'Перейти в канал @{chat.username}'),
    )
    if welcome:
        content = as_list(
            Text(f'Здравствуйте {message.from_user.full_name}!'),
            Text(f''),
            content
        )
    if isinstance(message, Message):
        await message.answer(
            text=content.as_markdown(),
            reply_markup=inline_menu,
        )
    else:
        call = message
        await call.message.edit_text(
            text=content.as_markdown(),
            reply_markup=inline_menu,
        )
