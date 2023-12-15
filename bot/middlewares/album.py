import asyncio
from typing import MutableMapping, Dict, Any, Callable, Awaitable, cast, Tuple, Optional, List

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from cachetools import TTLCache

from bot.custom_types.album import Media, Album
from bot.constants import DEFAULT_TTL_ALBUM_MIDDLEWARE, DEFAULT_LATENCY_ALBUM_MIDDLEWARE


class AlbumMiddleware(BaseMiddleware):
    def __init__(
            self,
            album_key: str = "album",
            latency: float = DEFAULT_LATENCY_ALBUM_MIDDLEWARE,
            ttl: float = DEFAULT_TTL_ALBUM_MIDDLEWARE,
    ) -> None:
        self.album_key = album_key
        self.latency = latency
        self.cache: MutableMapping[str, Dict[str, Any]] = TTLCache(maxsize=10_000, ttl=ttl)

    @classmethod
    def webhook_mode(cls, album_key: str = "album") -> "AlbumMiddleware":
        """
        In case updates are processed in the background (by default in BaseRequestHandler),
        just increase the delay.
        """
        return cls(album_key=album_key, latency=2, ttl=5)

    def sorted_medias(
            self,
            messages: List[Message],
    ) -> List[Media]:
        return [self.get_content(message)[0] for message in messages]

    @staticmethod
    def get_content(message: Message) -> Optional[Tuple[Media, str, str]]:
        content_type = message.content_type
        caption = message.caption if message.caption else ''
        if message.photo:
            return message.photo[-1], content_type, caption
        if message.video:
            return message.video, content_type, caption
        if message.audio:
            return message.audio, content_type, caption
        if message.document:
            return message.document, content_type, caption
        return None

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.media_group_id is not None:
            key = event.media_group_id
            media, content_type, caption = cast(Tuple[Media, str, str], self.get_content(event))
            # print(media)
            # print(content_type)

            if key in self.cache:
                if content_type not in self.cache[key]:
                    self.cache[key][content_type] = [media]
                    return None

                self.cache[key]["messages"].append(event)
                self.cache[key]["messages"] = sorted(self.cache[key]["messages"], key=lambda x: x.message_id)
                self.cache[key]["captions"].append(caption)
                # self.cache[key][content_type].append(media)
                self.cache[key][content_type] = self.sorted_medias(
                    self.cache[key]["messages"],
                )
                return None

            self.cache[key] = {
                content_type: [media],
                "messages": [event],
                "captions": [event.md_text],
            }

            await asyncio.sleep(self.latency)
            data[self.album_key] = Album.model_validate(
                self.cache[key], context={"bot": data["bot"]}
            )

        return await handler(event, data)
