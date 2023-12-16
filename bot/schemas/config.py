import os
import tomllib
from pathlib import Path
from typing import List

from pydantic import BaseModel


class TelegramConfig(BaseModel):
    bot_token: str
    db_name: str
    start_notify: bool
    start_notify_ids: List[str | int]
    channel_id: str | int
    support_username: str
    bot_username: str
    channel_username: str
    max_length_ads: int
    max_ads_per_day: int
    advertising: str
    advertising_every_ad: int
    reminder_if_no_activity_seconds: int


class CurseWordsConfig(BaseModel):
    file_path: str


class RedisConfig(BaseModel):
    host: str
    port: int


class PostgresConfig(BaseModel):
    host: str
    port: int
    login: str
    password: str


class Config(BaseModel):
    telegram: TelegramConfig
    redis: RedisConfig
    postgres: PostgresConfig
    curse_words: CurseWordsConfig

    @staticmethod
    def get(mode: str) -> "Config":
        return Config.model_validate(tomllib.loads(Path(f'config.{mode}.toml').read_text(encoding='utf-8')))
