import datetime

from app.db.engine import async_session
from app.db.models import UserBase, LotBase, Status

from sqlalchemy import select, BigInteger


async def set_lot(tg_id: BigInteger, starter_price: int, hours_exp: int, photo_id: str):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id==tg_id))
        session.add(LotBase(
            user_id =user.id,
            photo_id=photo_id,
            starter_price = starter_price,
            real_price = starter_price,
            moment_buy_price = starter_price + (starter_price / 100 * 20),
            completion_time = datetime.datetime.now() + datetime.timedelta(hours=hours_exp),
            seller = user.username,
            status = Status.bidding
        ))
        user.lots += 1
        await session.commit()

async def deposit_balance(tg_id: BigInteger, stars: int):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id==tg_id))
        user.balance += stars
        await session.commit()

async def get_data(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id==tg_id))
        return  user
