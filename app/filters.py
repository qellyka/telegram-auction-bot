from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

import app.db.requests as rq

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await rq.get_user_data(message.from_user.id)
        return user.is_admin

class IsAdminCb(BaseFilter):
    async def __call__(self, cb: CallbackQuery) -> bool:
        user = await rq.get_user_data(cb.from_user.id)
        return user.is_admin

class IsUser(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await rq.get_user_data(message.from_user.id)
        return not(user.is_admin)

class IsUserCb(BaseFilter):
    async def __call__(self, cb: CallbackQuery) -> bool:
        user = await rq.get_user_data(cb.from_user.id)
        return not (user.is_admin)