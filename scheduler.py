"""Автоматическая отправка отчёта в последний день месяца."""
import asyncio
import calendar
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import BufferedInputFile

from config import AUTO_REPORT_HOUR, TZ
from database import get_users, meta_get, meta_set
from reports import build_xlsx, summary_text


async def monthly_scheduler(bot: Bot):
    """Раз в минуту проверяет: не пора ли слать отчёт за месяц."""
    while True:
        try:
            now = datetime.now(TZ)
            last_day = calendar.monthrange(now.year, now.month)[1]
            key = f"sent:{now.year}-{now.month:02d}"  # метка «за этот месяц уже отправили»

            if now.day == last_day and now.hour >= AUTO_REPORT_HOUR and not meta_get(key):
                start_d = now.date().replace(day=1)
                end_d = now.date()
                title = f"Итоги месяца ({start_d.strftime('%m.%Y')})"

                for u in get_users():
                    try:
                        await bot.send_message(
                            u["chat_id"],
                            summary_text(u["user_id"], start_d, end_d, title),
                            parse_mode="HTML",
                        )
                        await bot.send_document(
                            u["chat_id"],
                            BufferedInputFile(
                                build_xlsx(u["user_id"], start_d, end_d),
                                filename=f"report_{now.year}-{now.month:02d}.xlsx",
                            ),
                            caption="📎 Отчёт за месяц",
                        )
                    except Exception as e:
                        logging.warning("Не удалось отправить %s: %s", u["user_id"], e)

                meta_set(key, "1")  # чтобы не отправлять повторно
        except Exception as e:
            logging.exception("Ошибка планировщика: %s", e)

        await asyncio.sleep(60)
