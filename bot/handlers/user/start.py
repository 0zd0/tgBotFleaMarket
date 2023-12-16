from typing import Any

from aiogram import Router, F, flags
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery
from aiogram.utils.formatting import as_list, Text, Bold, Underline

from bot.data.main_config import config
from bot.db.ad.model import AdModel
from bot.db.user.model import UserModel
from bot.enums.action import Action
from bot.filters.terms_of_use import IsAcceptTermsOfUseFilter
from bot.filters.user import RoleFilter
from bot.keyboards.default.menu import menu_keyboards
from bot.enums.db.role import ALL
from bot.keyboards.inline.menu import inline_menu
from bot.keyboards.inline.terms_of_use import accept_terms_keyboard, TermsOfUseCallback
from bot.loader import bot
from bot.middlewares.subscribe import SubscribeChannelMiddleware
from bot.utils.misc.menu import send_main_menu

router = Router()
router.message.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))
router.callback_query.middleware(SubscribeChannelMiddleware(channel_id=config.telegram.channel_id))


@router.message(
    F.chat.type == ChatType.PRIVATE,
    CommandStart(),
    any_state,
    RoleFilter(ALL),
    ~IsAcceptTermsOfUseFilter()
)
@flags.rate_limit(limit=3)
async def start_terms(
        message: Message,
        state: FSMContext,
) -> Any:
    await state.clear()
    content = as_list(
        Text(f'Добро пожаловать в бота @{(await bot.get_me()).username}'),
        Text(f''),
        Text(
            f'Данный бот поможет вам опубликовать объявление на канале '
            f'@{config.telegram.channel_username}!'
        ),
        Text(f''),
        Text(Bold(f'Начиная использовать данного бота, вы подтверждаете, что прочитали, поняли и согласны со всеми '
                  f'условиями и положениями настоящего пользовательского соглашения (далее - Соглашение). Если вы не '
                  f'согласны с условиями этого Соглашения, не начинайте использовать Бота.')),
        Text(f''),
        Text(Underline(Bold('Условия использования'))),
        Text(f''),
        Text(Bold(f'1. В Ваше объявление перед публикацией может быть добавлена реклама. Мы оставляем за собой право '
                  f'вставлять рекламные сообщения в ваши объявления без вашего предварительного уведомления или '
                  f'согласия. Сообщения, содержащие рекламу, не подлежат редактированию или удалению со стороны '
                  f'пользователя. Весь текст, картинки, и видео отправленные пользователем остаются неизменны.')),
        Text(f''),
        Text(Bold(f'2. Все пользователи соглашаются не публиковать оскорбительные, унижающие или провоцирующие '
                  f'сообщения или материалы. Недопустимо оскорблять других участников или администраторов бота. '
                  f'Пользователи, нарушающие эти условия, могут быть заблокированы или удалены из Бота.')),
        Text(f''),
        Text(Bold(f'3. Мы оставляем за собой право модерации всех публикаций, и в случае выявления нарушений правил '
                  f'и условий этого Соглашения, имеем право удалить или отредактировать любое объявление без '
                  f'предварительного уведомления.')),
        Text(f''),
        Text(Underline(Bold('Ответственность'))),
        Text(f''),
        Text(Bold(f'Вся информация и материалы, размещаемые вами через Бота, являются вашей ответственностью. Вы '
                  f'должны гарантировать, что они не нарушают действующего законодательства и не нарушают права '
                  f'третьих лиц.')),
        Text(f''),
        Text(Underline(Bold('Изменения в Соглашении'))),
        Text(f''),
        Text(Bold(f'Мы оставляем за собой право в любое время изменять или дополнять это Соглашение. Пожалуйста, '
                  f'регулярно проверяйте условия этого Соглашения для своевременного ознакомления с такими '
                  f'изменениями.')),
        Text(f''),
        Text(Bold(f'Пожалуйста, будьте уважительны и соблюдайте правила. Мы здесь, чтобы создать позитивное и '
                  f'продуктивное сообщество. Ваше сотрудничество и понимание очень ценятся!')),
    )
    await message.answer(
        text=content.as_markdown(),
        reply_markup=accept_terms_keyboard,
    )


@router.callback_query(
    F.message.chat.type == ChatType.PRIVATE,
    TermsOfUseCallback.filter(F.action == Action.accept),
    any_state,
    RoleFilter(ALL),
    ~IsAcceptTermsOfUseFilter()
)
async def accept_terms_of_use(
        call: CallbackQuery,
        user: UserModel,
) -> Any:
    await call.answer()
    await UserModel.accept_terms_of_use(user.id)
    content = as_list(
        Text(f'Спасибо за ваше согласие! Теперь вы можете использовать бота.'),
        Text(f''),
        Text(f'Нажмите /start'),
    )
    await call.message.answer(
        text=content.as_markdown(),
    )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    CommandStart(),
    any_state,
    RoleFilter(ALL),
    IsAcceptTermsOfUseFilter()
)
@flags.rate_limit(limit=3)
async def start(
        message: Message,
        state: FSMContext,
) -> Any:
    await state.clear()
    await send_main_menu(message, message.from_user, welcome=True)
