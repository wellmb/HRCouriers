from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hrcouriers.bot")


@dataclass(frozen=True)
class Vacancy:
    code: str
    title: str
    description: str
    ref_url: str


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required env: {name}")
    return value


def _safe_deep_code(raw: str | None) -> str | None:
    if not raw:
        return None
    token = raw.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{1,64}", token):
        return None
    return token


BOT_TOKEN = _required_env("BOT_TOKEN")
ADMIN_ID = int(_required_env("ADMIN_ID"))

VACANCIES: dict[str, Vacancy] = {
    "yandex": Vacancy("yandex", "Яндекс Еда", "Доставка из ресторанов и магазинов. Гибкий график и понятная мотивация.", _required_env("REF_YANDEX")),
    "kuper": Vacancy("kuper", "Купер", "Доставка продуктов и заказов из магазинов. Стабильный поток заказов в вашем районе.", _required_env("REF_KUPER")),
    "magnit": Vacancy("magnit", "Магнит", "Доставка заказов сети Магнит. Прозрачные условия и понятный формат работы.", _required_env("REF_MAGNIT")),
    "dodo": Vacancy("dodo", "Додо Пицца", "Доставка из пиццерий Додо: предсказуемые маршруты и стабильные смены.", _required_env("REF_DODO")),
    "samokat": Vacancy("samokat", "Самокат", "Быстрая доставка на коротких дистанциях с высокой оборачиваемостью заказов.", _required_env("REF_SAMOKAT")),
    "vkusno": Vacancy("vkusno", "Вкусно — и точка", "Доставка из ресторанов сети с устойчивым потоком заказов.", _required_env("REF_VKUSNO")),
    "pyaterochka": Vacancy("pyaterochka", "Пятерочка", "Доставка продуктов из магазинов у дома. Удобные смены и регулярные выплаты.", _required_env("REF_PYATEROCHKA")),
    "ozon": Vacancy("ozon", "Ozon", "Работа на доставке и складах Ozon с гибким графиком и стабильной загрузкой.", _required_env("REF_OZON")),
    "alfa": Vacancy("alfa", "Карта Альфа-Банка", "Карта для курьеров и самозанятых: удобно получать выплаты и управлять расходами.", _required_env("REF_ALFA")),
}

router = Router()
SUPPORT_THREADS: dict[int, int] = {}


def vacancy_button(vacancy: Vacancy) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"Перейти: {vacancy.title}", url=vacancy.ref_url)]]
    )


def all_vacancies_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for code in ("yandex", "kuper", "magnit", "dodo", "samokat", "vkusno", "pyaterochka", "ozon", "alfa"):
        vacancy = VACANCIES[code]
        rows.append([InlineKeyboardButton(text=vacancy.title, url=vacancy.ref_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def notify_admin_start(message: Message, start_code: str | None) -> None:
    user = message.from_user
    if not user:
        return
    await message.bot.send_message(
        ADMIN_ID,
        "\n".join(
            [
                "Новый /start",
                f"id: {user.id}",
                f"username: @{user.username}" if user.username else "username: —",
                f"name: {user.full_name}",
                f"deep_link: {start_code or 'none'}",
            ]
        ),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    code = _safe_deep_code(command.args)
    await notify_admin_start(message, code)
    if code and code in VACANCIES:
        vacancy = VACANCIES[code]
        await message.answer(
            f"**{vacancy.title}**\n\n{vacancy.description}",
            parse_mode="Markdown",
            reply_markup=vacancy_button(vacancy),
        )
        return

    await message.answer(
        "Привет! Выберите направление, и я сразу дам официальную ссылку для регистрации.",
        reply_markup=all_vacancies_keyboard(),
    )


@router.message(F.from_user.id == ADMIN_ID, F.reply_to_message, F.text, ~F.text.startswith("/"))
async def admin_reply(message: Message) -> None:
    reply = message.reply_to_message
    if not reply:
        await message.answer("Ответьте именно на пересланное сообщение пользователя.")
        return
    target_id = SUPPORT_THREADS.get(reply.message_id)
    if not target_id:
        await message.answer("Не вижу связанного пользователя для этого ответа.")
        return
    await message.bot.send_message(target_id, f"Ответ поддержки:\n{message.text}")
    await message.answer("Ответ отправлен пользователю.")


@router.message(F.from_user.id != ADMIN_ID, F.text & ~F.text.startswith("/"))
async def support_forward(message: Message) -> None:
    user = message.from_user
    username_line = f"username: @{user.username}" if user and user.username else "username: —"
    prefix = (
        "Сообщение в поддержку\n"
        f"id: {user.id if user else '—'}\n"
        f"name: {user.full_name if user else '—'}\n"
        f"{username_line}"
    )
    await message.bot.send_message(ADMIN_ID, prefix)
    forwarded = await message.forward(ADMIN_ID)
    if user:
        SUPPORT_THREADS[forwarded.message_id] = user.id
    await message.answer("Передал сообщение оператору. Ответ придет здесь.")


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message) -> None:
    if message.from_user and message.from_user.id == ADMIN_ID:
        return
    await message.answer("Неизвестная команда. Используйте /start.")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
