from enum import Enum

import emoji


class MainMenu(str, Enum):
    NEW_AD = f'Добавить объявление'
    MY_ADS = f'Мои объявления'
    SELECT_ACTION = f'Выберите пункт'
    MENU = f'Меню'


class MainMenuItemCallback(str, Enum):
    NEW_AD = f'new_ad'
    MY_ADS = f'my_ads'
    MAIN_MENU = f'main_menu'


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
    BACK_TO_MENU = f'Назад в меню'
    DELETE = f'{emoji.emojize(":cross_mark:")} Удалить'
    EDIT = f'{emoji.emojize(":pencil:")} Редактировать'
