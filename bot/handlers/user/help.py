from typing import Any

from aiogram import Router, F, flags
from aiogram.enums import ChatType
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message
from aiogram.utils.formatting import as_list, Text, Code

from bot.db.user.model import UserModel
from bot.enums.db.role import ALL
from bot.filters.user import RoleFilter
from bot.keyboards.default.menu import menu_keyboards

router = Router()


@router.message(
    F.chat.type == ChatType.PRIVATE,
    or_f(Command('help')),
    any_state,
    RoleFilter(ALL),
)
@flags.rate_limit(limit=3)
async def help_handler(
        message: Message,
        state: FSMContext,
        user: UserModel,
) -> Any:
    await state.clear()
    content = as_list(
        Text(Text(f'Ваш ID: '), Code(f'{message.from_user.id}'))
    )
    await message.answer(text=content.as_markdown(), reply_markup=menu_keyboards.get(user.role))
