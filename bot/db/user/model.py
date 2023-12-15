import datetime
from typing import Tuple, List

import pytz
from sqlalchemy import and_
from sqlalchemy.sql import expression

from bot.db.base.model import BaseModel
from bot.db.utils.enum import get_sql_enum
from bot.enums.db.role import Role, ALL
from bot.loader import db


class UserModel(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger(), primary_key=True, unique=True)
    name = db.Column(db.String)
    username = db.Column(db.String)
    role = db.Column(get_sql_enum(Role, 'role'), index=True)
    terms_of_use = db.Column(db.Boolean, server_default=expression.false())
    last_activity = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    reminder_activity = db.Column(db.Boolean, server_default=expression.false())

    @classmethod
    async def get_by_id(
            cls,
            tg_id: int | str
    ) -> "UserModel":
        return await cls.get(tg_id)

    @classmethod
    async def create_user(
            cls,
            tg_id: int | str,
            name: str,
            username: str | None = None,
            role: Role = Role.USER,
    ) -> "UserModel":
        return await cls.create(
            id=tg_id,
            name=name,
            username=username,
            role=role,
        )

    @classmethod
    async def get_all_old_activity(
            cls,
            non_activity_seconds: int
    ) -> List['UserModel']:
        non_activity_time = (datetime.datetime.now(tz=pytz.timezone("UTC")) -
                             datetime.timedelta(seconds=non_activity_seconds))
        return await (cls.query
                      .where(and_(
                            cls.last_activity <= non_activity_time,
                            cls.terms_of_use.is_(True),
                            cls.reminder_activity.is_(False),
                            cls.role.in_(ALL),
                        ))
                      .order_by(cls.created_at.asc())
                      .gino.all())

    @classmethod
    async def set_reminder(
            cls,
            user_id: int,
            reminder: bool = True
    ) -> None:
        await cls.update.values(reminder_activity=reminder).where(cls.id == user_id).gino.status()

    @classmethod
    async def create_or_update(
            cls,
            tg_id: int | str,
            name: str,
            username: str | None = None,
            change_last_activity: bool = False
    ) -> Tuple["UserModel", bool]:
        exist = await cls.get_by_id(tg_id)
        if exist:
            if change_last_activity:
                await exist.update(
                    name=name,
                    username=username,
                    last_activity=datetime.datetime.now(),
                    reminder_activity=False
                ).apply()
            elif exist.name != name or exist.username != username:
                await exist.update(
                    name=name,
                    username=username,
                ).apply()
            return exist, False
        else:
            return await cls.create_user(
                tg_id=tg_id,
                name=name,
                username=username,
                role=Role.USER
            ), True

    @classmethod
    async def update_role(
            cls,
            user_id: int,
            role: Role
    ) -> None:
        await cls.update.values(role=role).where(cls.id == user_id).gino.status()

    @classmethod
    async def get_all_by_role(
            cls,
            roles: List[Role]
    ) -> List['UserModel']:
        return await cls.query.where(and_(cls.role.in_(roles))).gino.all()

    @classmethod
    async def accept_terms_of_use(
            cls,
            user_id: int,
    ) -> None:
        await cls.update.values(terms_of_use=True).where(cls.id == user_id).gino.status()
