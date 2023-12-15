from enum import Enum
from typing import Type

from sqlalchemy import types


def get_sql_enum(enum: Type[Enum], name: str) -> types.Enum:
    return types.Enum(
        enum,
        name=name,
        values_callable=lambda obj: [e.value for e in obj]
    )
