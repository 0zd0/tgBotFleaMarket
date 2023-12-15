import asyncio
import logging

from bot.handlers.errors import errors_routers
from bot.handlers.user import user_handlers
from bot.loader import dp, bot
from bot.middlewares import ThrottlingMiddleware
from bot.middlewares.logger import LoggerMiddleware
from bot.middlewares.user import UserMiddleware
from bot.utils.startup import on_startup

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
               "[%(asctime)s] - %(name)s - %(message)s",
    )
    logging.getLogger('gino.engine._SAEngine').setLevel(logging.ERROR)
    logging.getLogger('apscheduler.executors.default').setLevel(logging.ERROR)
    dp.include_routers(
        *errors_routers,
        *user_handlers,
    )
    # dp.message.outer_middleware(LoggerMiddleware())

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(UserMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())

    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
