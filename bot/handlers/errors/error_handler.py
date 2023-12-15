import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import ErrorEvent

router = Router()


@router.errors()
async def errors_handler(error: ErrorEvent):
    if isinstance(error.exception, TelegramBadRequest):
        logging.exception(f'Bad Request: {error.exception} \nUpdate: {error.update}')
        return True

    if isinstance(error.exception, TelegramAPIError):
        logging.exception(f'TelegramAPIError: {error.exception} \nUpdate: {error.update}')
        return True

    logging.exception(f'Update: {error.update} \n{error.exception}')
