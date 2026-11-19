"""Все кнопки бота."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import EXPENSE_CATS, INCOME_CATS

# Тексты кнопок главного меню (по ним хэндлеры понимают, что нажали)
BTN_INCOME = "➕ Доход"
BTN_EXPENSE = "➖ Расход"
BTN_REPORT = "📊 Отчёт"
BTN_UNDO = "↩️ Удалить последнюю"

# Кнопки, которые всегда висят внизу экрана
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_INCOME), KeyboardButton(text=BTN_EXPENSE)],
        [KeyboardButton(text=BTN_REPORT), KeyboardButton(text=BTN_UNDO)],
    ],
    resize_keyboard=True,
)


def cats_kb(kind: str) -> InlineKeyboardMarkup:
    """Кнопки категорий под сообщением (разные для дохода и расхода)."""
    cats = INCOME_CATS if kind == "income" else EXPENSE_CATS
    rows, row = [], []
    for i, c in enumerate(cats):
        row.append(InlineKeyboardButton(text=c, callback_data=f"cat:{i}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def report_kb() -> InlineKeyboardMarkup:
    """Выбор периода отчёта."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сегодня", callback_data="rep:today"),
            InlineKeyboardButton(text="Неделя", callback_data="rep:week"),
        ],
        [
            InlineKeyboardButton(text="Этот месяц", callback_data="rep:month"),
            InlineKeyboardButton(text="Прошлый месяц", callback_data="rep:prev"),
        ],
    ])


def file_kb(period: str) -> InlineKeyboardMarkup:
    """Кнопки под готовым отчётом."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Скачать Excel", callback_data=f"xls:{period}")],
        [InlineKeyboardButton(text="⬅️ Другой период", callback_data="rep:menu")],
    ])
