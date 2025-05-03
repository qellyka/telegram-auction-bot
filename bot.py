import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.admin.handlers import admin_router
from app.auction.functions import background_tasks
from app.user.handlers import user_router
from app.db.engine import setup_db

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    await setup_db()
    dp.include_router(user_router)
    dp.include_router(admin_router)

    asyncio.create_task(background_tasks(bot=bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",)
    logger = logging.getLogger("aiogram")
    logger.setLevel(logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
    except ConnectionRefusedError:
        print('The database is not working or the connection link is incorrect')