from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, Message
from sqlalchemy import select

from app.db.models import UserBase
from app.db.engine import async_session

class UserDBCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
            user = event.from_user
            async with async_session() as session:
                db_user = await session.scalar(select(UserBase).where(UserBase.telegram_id == user.id))
                if not db_user:
                    session.add(UserBase(
                        telegram_id = user.id,
                        username = user.username,
                    ))
                    await session.commit()

            return await handler(event, data)


