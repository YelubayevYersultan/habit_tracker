import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from handlers import router

# Включаем логирование, чтобы видеть ошибки бота в консоли
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # Подключаем наши обработчики сообщений
    dp.include_router(router)

    print("Бот успешно запущен и слушает команды...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
