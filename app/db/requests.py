import datetime
from zoneinfo import ZoneInfo
import uuid

from datetime import datetime, timedelta

from app.db.engine import async_session
from app.db.models import UserBase, LotBase, LotStatus, LotModStatus

from sqlalchemy import select, BigInteger


async def set_lot(tid: BigInteger, starter_price: int, hours_exp: int, pid: str, blitz_price: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid)
            .with_for_update()
        )
        session.add(LotBase(
            user_id =user.id,
            uuid = uuid.uuid4().hex,
            photo_id=pid,
            starter_price = starter_price,
            real_price = starter_price,
            moment_buy_price = blitz_price,
            expired_at = datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None) + timedelta(hours=hours_exp),
            expired_time = hours_exp,
            seller = user.telegram_id,
            is_post = LotModStatus.PENDING,
            status = LotStatus.TRADING
        ))
        user.lots += 1
        await session.commit()

async def deposit_balance(tg_id: BigInteger, stars: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tg_id)
            .with_for_update()
        )
        user.balance += stars
        await session.commit()

async def get_user_data(tg_id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tg_id)
        )
        return  user

async def get_user_data_id(id: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.id==id)
        )
        return  user

async def get_lot_data(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
        )
        return lot

async def get_new_lots():
    async with async_session() as session:
        lots = await session.scalars(
            select(LotBase)
            .where(LotBase.is_post==LotModStatus.PENDING)
        )
        lots_list = [
            {key: getattr(lot, key) for key in lot.__table__.columns.keys()}
            for lot in lots
        ]
        return lots_list

async def approve_lot(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
            .with_for_update()
        )
        lot.is_post = LotModStatus.APPROVED
        lot.expired_at = datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None) + timedelta(hours=lot.expired_time)
        await session.commit()

async def reject_lot(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
            .with_for_update()
        )
        lot.is_post = LotModStatus.REJECTED
        await session.commit()

async def set_new_user(tid : BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid)
        )
        user.is_new = False
        await session.commit()

async def get_user_by_username(username: str):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.username==username)
        )
        return user

async def ban_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid)
            .with_for_update()
        )
        user.is_banned = True
        await session.commit()

async def unban_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id==tid)
            .with_for_update()
        )
        user.is_banned = False
        await session.commit()

async def get_lot_data_by_photo_id(pid: str):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.photo_id==pid)
        )
        return lot

async def get_blocked_users():
    async with async_session() as session:
        users = await session.scalars(
            select(UserBase)
            .where(UserBase.is_banned == True)
        )
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
        lot =  await session.scalar(
            select(LotBase)
            .where(LotBase.is_post == LotModStatus.PENDING, LotBase.id > current_lot_id)
            .order_by(LotBase.id.asc())
            .limit(1)
        )
        return lot

async def get_previous_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(
            select(LotBase)
            .where(LotBase.is_post == LotModStatus.PENDING, LotBase.id < current_lot_id)
            .order_by(LotBase.id.desc())
            .limit(1)
        )

async def get_lot_by_uuid(uuid: str):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.uuid==uuid)
        )
        return lot

async def set_lot_applicant(lot_id: int, applicant: int):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
            .with_for_update()
        )
        lot.applicant = applicant
        await session.commit()

async def get_lot_applicant(lot_id: int):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
        )
        return lot.applicant

async def set_new_lot_price(lot_id: int, bid: int):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
            .with_for_update()
        )
        lot.real_price += bid
        await session.commit()

async def set_message_id(lot_id: int, message_id: int):
    async with async_session() as session:
        lot = await session.scalar(
            select(LotBase)
            .where(LotBase.id==lot_id)
            .with_for_update()
        )
        lot.message_id = message_id
        await session.commit()

async def increase_balance(tg_id: BigInteger, bid: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id == tg_id)
            .with_for_update()
        )
        print('USUS')
        user.balance += bid
        await session.commit()

async def decrease_balance(tg_id: BigInteger, bid: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id == tg_id)
            .with_for_update()
        )
        print('USUS')
        user.balance -= bid
        await session.commit()

async def buy_now(lot_id, user_id):
    async with async_session() as session:
        lot = await session.scalar(
                select(LotBase)
                .where(LotBase.id==lot_id)
                .with_for_update()
        )
        lot.status = LotStatus.SOLD
        lot.buyer = user_id
        lot.applicant = user_id
        await session.commit()