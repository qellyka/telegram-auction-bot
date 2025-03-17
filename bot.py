import asyncio
import logging

from aiogram import Bot, Dispatcher, F

from app.user.handlers import user_router
from app.db.engine import setup_db

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await setup_db()
    dp.include_router(user_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')