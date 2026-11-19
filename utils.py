"""Мелкие помощники: форматирование суммы, разбор числа, периоды."""
from datetime import datetime, date, timedelta

from config import TZ


def fmt(n: float) -> str:
    """1500000 -> '1 500 000'"""
    if abs(n - round(n)) < 0.005:
        return f"{int(round(n)):,}".replace(",", " ")
    return f"{n:,.2f}".replace(",", " ")


def parse_amount(text: str):
    """Понимает '150000', '150 000', '1500,50'. Если не число или <= 0 — вернёт None."""
    t = text.strip().replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return v if v > 0 else None


def period_range(period: str):
    """Возвращает (начало, конец, название) для периода отчёта."""
    today = datetime.now(TZ).date()
    if period == "today":
        return today, today, "Сегодня"
    if period == "week":  # с понедельника по сегодня
        return today - timedelta(days=today.weekday()), today, "Эта неделя"
    if period == "month":  # с 1 числа по сегодня
        return today.replace(day=1), today, "Этот месяц"
    if period == "prev":  # прошлый месяц целиком
        last_prev = today.replace(day=1) - timedelta(days=1)
        return last_prev.replace(day=1), last_prev, "Прошлый месяц"
    raise ValueError(period)
