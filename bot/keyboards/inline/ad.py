import math
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.constants import LIMIT_ADS_ON_PAGE
from bot.db.ad.model import AdModel
from bot.enums.action import Action
from bot.enums.menu import Buttons, Cancel, MainMenuItemCallback
from bot.keyboards.inline.menu import MenuItemCallback


class NewAdCallback(CallbackData, prefix='new_ad'):
    action: Action


class AdListControlCallback(CallbackData, prefix="ad_list_control"):
    page: int
    action: Action


class AdListActionCallback(CallbackData, prefix="ad_list_action"):
    action: Action
    page: int
    ad_id: int


class AdActionCallback(CallbackData, prefix="ad"):
    action: Action
    page: int
    ad_id: int


new_ad_skip_images_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=Buttons.SKIP.value,
                callback_data=NewAdCallback(action=Action.skip).pack()
            )
        ]
    ]
)

new_ad_public_images_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=Buttons.PUBLIC.value,
                callback_data=NewAdCallback(action=Action.public).pack()
            )
        ]
    ]
)


def get_back_to_menu_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=Buttons.BACK_TO_MENU.value,
        callback_data=MenuItemCallback(item=MainMenuItemCallback.MAIN_MENU).pack()
    )
    builder.adjust(1)
    return builder


def get_ads_list_control_keyboard(
        page: int,
        total_pages: int,
        offset: int,
) -> InlineKeyboardBuilder:
    real_page = page + 1
    builder = InlineKeyboardBuilder()
    button_prev = InlineKeyboardButton(
        text=Buttons.PREV.value,
        callback_data=AdListControlCallback(action=Action.prev, page=page - 1).pack()
    )
    button_next = InlineKeyboardButton(
        text=Buttons.NEXT.value,
        callback_data=AdListControlCallback(action=Action.next, page=page + 1).pack()
    )
    if offset > 0:
        builder.add(button_prev)
    if total_pages > 1:
        builder.button(text=f'{real_page} / {total_pages}', callback_data='null')
    if total_pages > real_page:
        builder.add(button_next)
    builder.adjust(3)
    builder.attach(get_back_to_menu_keyboard())
    return builder


def get_ads_list_keyboard(
        ads: List[AdModel],
        count_ads: int,
        page: int,
        offset: int,
        limit: int = LIMIT_ADS_ON_PAGE,
) -> InlineKeyboardBuilder:
    total_pages = math.ceil(count_ads / limit)
    control = get_ads_list_control_keyboard(page, total_pages, offset)
    builder = InlineKeyboardBuilder()
    for ad in ads:
        builder.button(
            text=ad.created_at.strftime("%H:%M %d.%m.%Y (%Z)"),
            callback_data=AdListActionCallback(action=Action.toggle, ad_id=ad.id, page=page)
        )
    builder.adjust(1)
    builder.attach(control)
    return builder


def get_ad_actions_keyboard(
        ad: AdModel,
        page: int,
) -> InlineKeyboardBuilder:
    last = InlineKeyboardBuilder()
    actions = InlineKeyboardBuilder()
    actions.button(text=Buttons.DELETE.value, callback_data=AdActionCallback(action=Action.delete, page=page,
                                                                             ad_id=ad.id))
    actions.button(text=Buttons.EDIT.value, callback_data=AdActionCallback(action=Action.edit, page=page,
                                                                           ad_id=ad.id))
    actions.adjust(2)
    last.button(text=Buttons.BACK.value, callback_data=AdActionCallback(action=Action.back, page=page,
                                                                        ad_id=ad.id))
    last.adjust(1)
    actions.attach(last)
    return actions


def get_cancel_ad_action_keyboard(
        ad_id: int,
        page: int,
) -> InlineKeyboardBuilder:
    cancel = InlineKeyboardBuilder()
    cancel.button(text=Cancel.CANCEL.value, callback_data=AdActionCallback(action=Action.cancel, page=page,
                                                                           ad_id=ad_id))
    cancel.adjust(1)
    return cancel
