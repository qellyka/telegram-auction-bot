from aiogram.filters import BaseFilter
from aiogram.types import Message

import app.db.requests as rq

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await rq.get_data(message.from_user.id)
        return user.is_admin

class IsUser(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await rq.get_data(message.from_user.id)
        return not(user.is_admin)