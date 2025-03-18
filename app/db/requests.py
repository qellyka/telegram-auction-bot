import datetime
from dataclasses import asdict

from app.db.engine import async_session
from app.db.models import UserBase, LotBase, LotStatus, LotModStatus

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
            is_post = LotModStatus.PENDING,
            status = LotStatus.bidding
        ))
        user.lots += 1
        await session.commit()

async def deposit_balance(tg_id: BigInteger, stars: int):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id==tg_id))
        user.balance += stars
        await session.commit()

async def get_user_data(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id==tg_id))
        return  user

async def get_user_data_id(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.id==tid))
        return  user

async def get_lot_data(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id==lot_id))
        return lot

async def get_new_lots():
    async with async_session() as session:
        lots = await session.scalars(select(LotBase).where(LotBase.is_post==LotModStatus.PENDING))
        lots_list = [
            {key: getattr(lot, key) for key in lot.__table__.columns.keys()}
            for lot in lots
        ]
        print('\n\n\n\n')
        print(lots_list)
        print('\n\n\n\n')
        return lots_list

async def approve_lot(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id==lot_id))
        lot.is_post = LotModStatus.APPROVED
        await session.commit()

async def reject_lot(lot_id: BigInteger, tg_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id==lot_id))
        lot.is_post = LotModStatus.REJECTED
        user = await get_user_data(tg_id)
        session.merge(user)
        user.lots =  user.lots - 1
        await session.commit()

async def set_new_user(user):
    async with async_session() as session:
        user.is_new = False
        await session.commit()