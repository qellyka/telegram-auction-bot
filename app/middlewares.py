import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import Message, CallbackQuery, Update
from sqlalchemy import select

import app.admin.keyboards as kb

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
                if not user.username:
                    await event.answer('Извините, но у вас отсутствует username. Для того чтобы пользоваться ботом, создайте себе username, после чего повторите команду.')
                    raise CancelHandler()
                elif not db_user:
                    session.add(UserBase(
                        telegram_id = user.id,
                        username = user.username,
                    ))
                    await session.commit()

            return await handler(event, data)

class UserBanCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
            user = event.from_user
            async with async_session() as session:
                db_user = await session.scalar(select(UserBase).where(UserBase.telegram_id == user.id))
                if db_user.is_banned:
                    await event.answer(text="Похоже вы забанены, если вы считаете, что бан был выдан по ошибке, советуем обратиться в тех. поддержку.",
                                       reply_markup=kb.tech_bot_menu)
                    raise CancelHandler()

            return await handler(event, data)

class UserBanCheckMiddlewareCB(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        async with async_session() as session:
            db_user = await session.scalar(
                select(UserBase).where(UserBase.telegram_id == user.id)
            )
            if db_user and db_user.is_banned:
                await event.answer(
                    text="Похоже, вы забанены. Если вы считаете, что бан был выдан по ошибке, советуем обратиться в техподдержку.",
                    reply_markup=kb.tech_bot_menu,
                    show_alert=True
                )
                raise CancelHandler()

        return await handler(event, data)