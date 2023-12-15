import datetime
from typing import List

import pytz
from aiogram.types import MessageEntity
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import expression

from bot.constants import LIMIT_ADS_ON_PAGE
from bot.db.base.model import BaseModel
from bot.loader import db
from bot.schemas.ad import NewAdModel, UtilsAdModel


class AdModel(BaseModel):
    __tablename__ = 'ads'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True, unique=True)
    user_id = db.Column(None, db.ForeignKey('users.id'))
    text = db.Column(db.String)
    entities = db.Column(JSON)
    photo_ids = db.Column(db.ARRAY(db.String))
    channel_message_id = db.Column(db.Integer)
    text_advertising = db.Column(db.String)
    archived = db.Column(db.Boolean(), server_default=expression.false(), nullable=False)

    @classmethod
    async def create_ad(
            cls,
            user_id: int,
            data: NewAdModel
    ) -> 'AdModel':
        return await cls.create(
            user_id=user_id,
            **data.model_dump()
        )

    @classmethod
    async def get_by_id(
            cls,
            ad_id: int
    ) -> 'AdModel':
        return await cls.get(ad_id)

    @classmethod
    async def get_last(
            cls,
            limit: int,
    ) -> List['AdModel']:
        return await cls.query.order_by(cls.created_at.desc()).limit(limit).gino.all()

    @classmethod
    async def ad_archive(
            cls,
            ad_id: int
    ):
        await cls.update.values(archived=True).where(cls.id == ad_id).gino.status()

    @classmethod
    async def edit_text(
            cls,
            ad_id: int,
            text: str,
            entities: List[MessageEntity],
    ):
        await (cls.update
               .values(text=text, entities=UtilsAdModel.get_entities_json(entities))
               .where(cls.id == ad_id)
               .gino.status())

    @classmethod
    async def get_count_all_ads_by_user(
            cls,
            user_id: int,
            archived: bool = False,
    ) -> int:
        return await ((db.select([db.func.count()])
                       .where(and_(cls.user_id == user_id, cls.archived.is_(archived))))
                      .gino.scalar())

    @classmethod
    async def get_all_ads_by_user(
            cls,
            user_id: int,
            archived: bool = False,
            limit: int = LIMIT_ADS_ON_PAGE,
            offset: int = 0
    ) -> List['AdModel']:
        return await (cls.query
                      .where(and_(cls.user_id == user_id, cls.archived.is_(archived)))
                      .order_by(cls.created_at.asc())
                      # .limit(limit)
                      .limit(limit)
                      .offset(offset)
                      .gino.all())

    @classmethod
    async def get_ads_day_by_user(
            cls,
            user_id: int,
    ) -> List['AdModel']:
        one_day_ago = datetime.datetime.now(tz=pytz.timezone("UTC")) - datetime.timedelta(days=1)
        return await (cls.query.where(and_(cls.user_id == user_id, cls.created_at >= one_day_ago))
                      .order_by(cls.created_at.asc()).gino.all())
