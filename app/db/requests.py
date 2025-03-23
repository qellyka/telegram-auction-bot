import datetime
from zoneinfo import ZoneInfo

from app.db.engine import async_session
from app.db.models import UserBase, LotBase, LotStatus, LotModStatus

from sqlalchemy import select, BigInteger


async def set_lot(tid: BigInteger, starter_price: int, hours_exp: int, pid: str, blitz_price: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid))
        session.add(LotBase(
            user_id =user.id,
            photo_id=pid,
            starter_price = starter_price,
            real_price = starter_price,
            moment_buy_price = blitz_price,
            expired_at = datetime.datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None) + datetime.timedelta(hours=hours_exp),
            expired_time = hours_exp,
            seller = user.username,
            is_post = LotModStatus.PENDING,
            status = LotStatus.TRADING
        ))
        user.lots += 1
        await session.commit()

async def deposit_balance(tg_id: BigInteger, stars: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tg_id))
        user.balance += stars
        await session.commit()

async def get_user_data(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tg_id))
        return  user

async def get_user_data_id(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.id==tid))
        return  user

async def get_lot_data(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id))
        return lot

async def get_new_lots():
    async with async_session() as session:
        lots = await session.scalars(
            select(LotBase)
            .where(LotBase.is_post==LotModStatus.PENDING))
        lots_list = [
            {key: getattr(lot, key) for key in lot.__table__.columns.keys()}
            for lot in lots
        ]
        return lots_list

async def approve_lot(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id))
        lot.is_post = LotModStatus.APPROVED
        lot.expired_at = datetime.datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None) + datetime.timedelta(hours=lot.expired_time)
        await session.commit()

async def reject_lot(lot_id: BigInteger, tg_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id))
        lot.is_post = LotModStatus.REJECTED
        await session.commit()

async def set_new_user(tid : BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid))
        user.is_new = False
        await session.commit()

async def get_user_by_username(username: str):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.username==username))
        return user

async def ban_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid))
        user.is_banned = True
        await session.commit()

async def unban_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid))
        user.is_banned = False
        await session.commit()

async def get_lot_data_by_photo_id(pid: str):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.photo_id==pid))
        return lot

async def get_blocked_users():
    async with async_session() as session:
        users = await session.scalars(
            select(UserBase)
            .where(UserBase.is_banned == True))
        users_list = [
            {key: getattr(user, key) for key in user.__table__.columns.keys()}
            for user in users
        ]
        return users_list

async def get_first_new_lot():
    async with async_session() as session:
        return await session.scalar(
            select(LotBase)
            .where(LotBase.is_post == LotModStatus.PENDING)
            .order_by(LotBase.id.asc())
            .limit(1)
        )

async def get_next_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(
            select(LotBase)
            .where(LotBase.is_post == LotModStatus.PENDING, LotBase.id > current_lot_id)
            .order_by(LotBase.id.asc())
            .limit(1)
        )

async def get_previous_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(
            select(LotBase)
            .where(LotBase.is_post == LotModStatus.PENDING, LotBase.id < current_lot_id)
            .order_by(LotBase.id.desc())
            .limit(1)
        )