from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from gino import Gino
from redis.asyncio import Redis

from bot.data.main_config import config

redis = Redis(host=config.redis.host, port=config.redis.port)
storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_bot_id=True))
dp = Dispatcher(storage=storage)
bot = Bot(token=config.telegram.bot_token, parse_mode=ParseMode.MARKDOWN_V2)
db = Gino()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
