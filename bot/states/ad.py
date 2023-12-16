from aiogram.fsm.state import StatesGroup, State


class NewAdState(StatesGroup):
    TEXT = State()
    MEDIA = State()


class EditAdTextState(StatesGroup):
    NEW_TEXT = State()


class DuplicateAdTextState(StatesGroup):
    NEW_TEXT = State()
