from typing import List, Optional, Any, Dict

from aiogram.types import MessageEntity
from pydantic import BaseModel


class UtilsAdModel:
    @staticmethod
    def get_entities_json(
            entities: List[MessageEntity]
    ) -> List[Dict[str, Any]]:
        return [entity.model_dump() for entity in entities or []]

    @staticmethod
    def get_entities_obj(
            entities: List[Dict[str, Any]]
    ) -> List[MessageEntity]:
        return [MessageEntity.model_validate(entity) for entity in entities]


class NewAdModel(BaseModel, UtilsAdModel):
    text: str = ''
    entities: Optional[List[MessageEntity]] = None
    photo_ids: Optional[List[str]] = None
    channel_message_id: Optional[int] = None
    text_advertising: Optional[str] = None
    user_name: Optional[str] = None

    def get_entities_to_json(
            self
    ) -> List[Dict[str, Any]]:
        return self.get_entities_json(entities=self.entities)


class EditAdTextModel(BaseModel, UtilsAdModel):
    ad_id: int
    page: int
    cancel_message_chat_id: int
    cancel_message_id: int
