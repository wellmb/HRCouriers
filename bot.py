"""
HRCouriers — Telegram-бот-рекрутер (aiogram 3.x).
Сбор ФИО и города, меню вакансий, пересылка обращений админу и ответ через ответ на пересылку или /answer.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Final

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import BaseFilter, Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Загрузка переменных окружения
# -----------------------------------------------------------------------------
load_dotenv()

BOT_TOKEN: Final[str | None] = os.getenv("8781140398:AAHWrFesfBo_jN97DS5FF9LWQMZv6jQD9f8")

# -----------------------------------------------------------------------------
# Заглушки реферальных ссылок — замените на свои рабочие URL (или задайте в .env)
# -----------------------------------------------------------------------------
REF_LINK_YANDEX_EDA: Final[str] = os.getenv(
    "REF_LINK_YANDEX_EDA",
    "https://example.com/yandex-food-referral-stub",
)
REF_LINK_KUPER: Final[str] = os.getenv(
    "REF_LINK_KUPER",
    "https://reg.eda.yandex.ru/?advertisement_campaign=forms_for_agents&user_invite_code=c1c9326558b7475f946c9118c0937a69&utm_content=blank&utm_campaign=HRCouriersSITE&promo_img_key=promo1",
)
REF_LINK_MAGNIT_MARKET: Final[str] = os.getenv(
    "REF_LINK_MAGNIT_MARKET",
    "https://example.com/magnit-market-referral-stub",
)
REF_LINK_ALFA: Final[str] = os.getenv(
    "REF_LINK_ALFA",
    "https://example.com/alfa-bank-referral-stub",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hrcouriers.bot")


class RegistrationStates(StatesGroup):
    """Этапы первичной анкеты после /start."""

    waiting_full_name = State()
    waiting_city = State()


class IsAdmin(BaseFilter):
    """Пропускает только сообщения от указанного администратора."""

    def __init__(self, admin_id: int) -> None:
        self.admin_id = admin_id

    async def __call__(self, message: Message) -> bool:
        uid = message.from_user.id if message.from_user else None
        return uid == self.admin_id


def vacancies_keyboard() -> InlineKeyboardMarkup:
    """Меню вакансий — те же бренды, что на сайте (+ Альфа)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Яндекс Еда", url=REF_LINK_YANDEX_EDA)],
            [InlineKeyboardButton(text="Купер", url=REF_LINK_KUPER)],
            [InlineKeyboardButton(text="Магнит Маркет", url=REF_LINK_MAGNIT_MARKET)],
            [InlineKeyboardButton(text="Карта Альфа-Банка", url=REF_LINK_ALFA)],
        ]
    )


def _extract_deep_link(args: str | None) -> str | None:
    """Безопасное извлечение payload из /start (deep link с сайта)."""
    if not args:
        return None
    token = args.strip()
    if not token:
        return None
    # Допустимые символы для параметра start по правилам Telegram
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", token):
        return None
    return token


def build_router(admin_id: int) -> Router:
    """Собираем роутер с замыканием на admin_id (фильтры IsAdmin)."""
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext, command: CommandObject) -> None:
        """Старт бота: учитываем deep link (?start=...) и запускаем анкету."""
        payload = _extract_deep_link(command.args)
        await state.clear()
        if payload:
            await state.update_data(source=payload)
            logger.info("Старт с deep link: user=%s payload=%s", message.from_user.id, payload)

        await state.set_state(RegistrationStates.waiting_full_name)
        await message.answer(
            "Здравствуйте! Я помогу с подбором вакансии для курьера.\n\n"
            "Пожалуйста, напишите ваше **ФИО** одним сообщением (как в документе).",
            parse_mode="Markdown",
        )

    @router.message(RegistrationStates.waiting_full_name, F.text)
    async def process_full_name(message: Message, state: FSMContext) -> None:
        """Сохраняем ФИО и спрашиваем город."""
        full_name = message.text.strip()
        if len(full_name) < 3:
            await message.answer("ФИО кажется слишком коротким. Напишите, пожалуйста, полностью.")
            return
        await state.update_data(full_name=full_name)
        await state.set_state(RegistrationStates.waiting_city)
        await message.answer(
            "Спасибо! Укажите **город**, в котором планируете работать.",
            parse_mode="Markdown",
        )

    @router.message(RegistrationStates.waiting_city, F.text)
    async def process_city(message: Message, state: FSMContext) -> None:
        """Сохраняем город и показываем меню вакансий."""
        city = message.text.strip()
        if len(city) < 2:
            await message.answer("Город не распознан. Напишите название ещё раз.")
            return
        data = await state.get_data()
        await state.clear()
        await message.answer(
            f"Принято: **{data.get('full_name', '—')}**, город **{city}**.\n\n"
            "Ниже — актуальные направления. Нажмите кнопку, чтобы перейти по партнёрской ссылке.",
            parse_mode="Markdown",
            reply_markup=vacancies_keyboard(),
        )

    @router.message(RegistrationStates.waiting_full_name)
    @router.message(RegistrationStates.waiting_city)
    async def registration_need_text(message: Message) -> None:
        """На этапе анкеты принимаем только текст."""
        await message.answer("Сейчас нужен текстовый ответ (без голосовых и стикеров).")

    @router.message(IsAdmin(admin_id), F.reply_to_message, F.text, ~Command())
    async def admin_reply_via_forward(message: Message) -> None:
        """
        Админ отвечает **ответом** на пересланное ботом сообщение —
        текст уходит пользователю от имени бота.
        """
        fwd = message.reply_to_message
        if not fwd or not fwd.forward_from:
            return
        target_id = fwd.forward_from.id
        try:
            await message.bot.send_message(
                target_id,
                "Ответ службы поддержки:\n" + message.text,
            )
            await message.answer("Сообщение доставлено пользователю.")
        except Exception as exc:  # noqa: BLE001 — показываем админу ошибку доставки
            logger.exception("Не удалось отправить ответ пользователю %s", target_id)
            await message.answer(f"Не удалось доставить: {exc}")

    @router.message(IsAdmin(admin_id), Command("answer"))
    async def cmd_answer(message: Message, command: CommandObject) -> None:
        """
        Ручной ответ: /answer <telegram_id> <текст сообщения>
        Пример: /answer 123456789 Здравствуйте, заявка принята.
        """
        raw = (command.args or "").strip()
        if not raw:
            await message.answer(
                "Формат: `/answer <telegram_id> <текст>`\n"
                "Пример: `/answer 123456789 Заявка принята`",
                parse_mode="Markdown",
            )
            return
        parts = raw.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Укажите и id пользователя, и текст ответа после него.")
            return
        user_id_str, body = parts[0], parts[1]
        try:
            target_id = int(user_id_str)
        except ValueError:
            await message.answer("telegram_id должен быть числом.")
            return
        try:
            await message.bot.send_message(target_id, "Ответ службы поддержки:\n" + body)
            await message.answer("Сообщение отправлено.")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Ошибка /answer для %s", target_id)
            await message.answer(f"Ошибка отправки: {exc}")

    @router.message(StateFilter(None), F.text.startswith("/"), ~CommandStart())
    async def unknown_command(message: Message) -> None:
        """Подсказка по неизвестным командам (когда пользователь уже не в анкете)."""
        if message.from_user and message.from_user.id == admin_id:
            return
        await message.answer("Неизвестная команда. Напишите /start, чтобы начать заново.")

    @router.message(StateFilter(None), F.chat.type == "private")
    async def forward_user_message_to_admin(message: Message) -> None:
        """
        Простая поддержка: пересылаем сообщения пользователя админу.
        Состояние FSM должно быть пустым (анкета пройдена).
        """
        if message.from_user and message.from_user.id == admin_id:
            return
        try:
            await message.forward(admin_id)
            await message.answer("Сообщение передано оператору. Мы ответим в ближайшее время.")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Не удалось переслать сообщение админу")
            await message.answer(f"Не удалось связаться с оператором: {exc}")

    return router


def _parse_admin_id(raw: str | None) -> int:
    if raw is None or not str(raw).strip():
        raise RuntimeError("В .env не задан ADMIN_TELEGRAM_ID (ваш числовой id в Telegram).")
    return int(str(raw).strip())


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Укажите BOT_TOKEN в файле .env")

    admin_id = _parse_admin_id(os.getenv("ADMIN_TELEGRAM_ID"))

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router(admin_id))

    bot = Bot(token=BOT_TOKEN)
    logger.info("Бот запущен. ADMIN_TELEGRAM_ID=%s", admin_id)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
