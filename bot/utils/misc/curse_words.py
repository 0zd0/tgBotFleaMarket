from typing import List

import aiofiles


async def get_curse_words(file_path: str) -> List[str]:
    async with aiofiles.open(file_path, "r", encoding='utf-8') as f:
        contents = await f.read()
        return contents.split('\n')
