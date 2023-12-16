from typing import Any

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery

from bot.data.main_config import config
from bot.db.user.model import UserModel
from bot.enums.db.role import ALL
from bot.enums.menu import MainMenuItemCallback
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.keyboards.inline.menu import MenuItemCallback
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.utils.misc.menu import send_main_menu

router = Router()
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    MenuItemCallback.filter(F.item == MainMenuItemCallback.MAIN_MENU),
    any_state,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter()
)
async def to_main_menu(
        call: CallbackQuery,
        state: FSMContext,
        user: UserModel,
) -> Any:
    await state.clear()
    await send_main_menu(call)
