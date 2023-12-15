import datetime

from aiogram import Bot

from bot.data.main_config import config
from bot.db.utils.bind import get_bind_config
from bot.loader import db, scheduler
from bot.utils.bot_commands import set_default_commands
from bot.utils.notify import on_startup_notify
from bot.utils.scheduler.reminder import reminder_old_activity


async def init_db_startup():
    await db.set_bind(get_bind_config(config.postgres, config.telegram.db_name))


async def init_scheduler():
    scheduler.start()
    scheduler.remove_all_jobs()
    scheduler.add_job(
        reminder_old_activity,
        'interval',
        seconds=10,
        coalesce=True,
        max_instances=1,
        replace_existing=True,
        next_run_time=datetime.datetime.now()
    )
    scheduler.print_jobs()


async def on_startup(bot: Bot) -> None:
    await init_db_startup()
    await set_default_commands(bot)
    if config.telegram.start_notify:
        await on_startup_notify(bot, config.telegram.start_notify_ids)
    await init_scheduler()
