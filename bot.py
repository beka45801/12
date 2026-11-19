"""Запуск бота: python bot.py"""
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db
from handlers import router
from scheduler import monthly_scheduler

logging.basicConfig(level=logging.INFO)


async def main():
    init_db()                      # создаём базу, если её нет
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)      # подключаем обработчики
    asyncio.create_task(monthly_scheduler(bot))  # фоновая проверка автоотчёта
    await dp.start_polling(bot)    # бот начинает слушать сообщения


if __name__ == "__main__":
    asyncio.run(main())
