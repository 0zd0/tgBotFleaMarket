from enum import Enum

import emoji


class MainMenu(str, Enum):
    NEW_AD = f'Добавить объявление'
    MY_ADS = f'Мои объявления'
    SELECT_ACTION = f'Выберите действие:'


class Cancel(str, Enum):
    CANCEL = f'{emoji.emojize(":cross_mark:")} Отмена'


class Buttons(str, Enum):
    ACCEPT_TERMS = f'Я все прочитал(а), с правилами согласен(на)'
    SKIP = f'Пропустить'
    ACCEPT = f'Подтвердить'
    PUBLIC = f'Опубликовать'
    PREV = f'← Предыдущая'
    NEXT = f'Следующая →'
    BACK = f'Назад'
    DELETE = f'{emoji.emojize(":cross_mark:")} Удалить'
    EDIT = f'{emoji.emojize(":pencil:")} Редактировать'
