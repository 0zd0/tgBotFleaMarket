import asyncio
import logging
import traceback

from aiogram.utils.formatting import as_list, Text

from bot.constants import REMINDER_IF_NO_ACTIVITY_SECONDS
from bot.data.main_config import config
from bot.db.user.model import UserModel
from bot.loader import bot


async def reminder_old_activity():
    users = await UserModel.get_all_old_activity(REMINDER_IF_NO_ACTIVITY_SECONDS)
    for user in users:
        try:
            content = as_list(
                Text(f'Вы долго не пользовались ботом. Если захотите вернуться, нажмите /start'),
                Text(),
                Text(f'Администратор группы @{config.telegram.support_username}'),
            )
            await bot.send_message(
                chat_id=user.id,
                text=content.as_markdown(),
                disable_web_page_preview=True,
            )
        except (Exception,) as e:
            logging.error(f'Ошибка при отправке сообщения юзеру #id{user.id}')
            traceback.print_exc()
        finally:
            await UserModel.set_reminder(user.id)
            await asyncio.sleep(0.5)
