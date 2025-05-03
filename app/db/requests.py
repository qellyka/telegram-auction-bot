from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import uuid

from sqlalchemy import select, BigInteger, func

from app.db.engine import async_session
from app.db.models import (
    UserBase,
    LotBase,
    LotStatus,
    LotModStatus,
    ReferralBase,
    WarnBase
)

# ----------------- LOT FUNCTIONS -----------------

async def set_lot(tid: BigInteger, starter_price: int, hours_exp: int, pid: str, blitz_price: int):
    async with async_session() as session:
        user = await session.scalar(
            select(UserBase)
            .where(UserBase.telegram_id == tid)
            .with_for_update()
        )
        session.add(LotBase(
            user_id=user.id,
            uuid=uuid.uuid4().hex,
            photo_id=pid,
            starter_price=starter_price,
            real_price=starter_price,
            moment_buy_price=blitz_price,
            expired_at=datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None) + timedelta(hours=hours_exp),
            expired_time=hours_exp,
            seller=user.telegram_id,
            is_post=LotModStatus.PENDING,
            status=LotStatus.TRADING
        ))
        user.lots += 1
        await session.commit()

async def get_lot_by_uuid(uuid: str):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.uuid == uuid))

async def get_lot_data(lot_id: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.id == lot_id))

async def get_lot_data_by_photo_id(pid: str):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.photo_id == pid))

async def approve_lot(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id).with_for_update())
        lot.is_post = LotModStatus.APPROVED
        lot.expired_at = datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None) + timedelta(hours=lot.expired_time)
        await session.commit()

async def reject_lot(lot_id: BigInteger):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id).with_for_update())
        lot.is_post = LotModStatus.REJECTED
        await session.commit()

async def get_new_lots():
    async with async_session() as session:
        lots = await session.scalars(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING))
        return [{key: getattr(lot, key) for key in lot.__table__.columns.keys()} for lot in lots]

async def get_first_new_lot():
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING).order_by(LotBase.id.asc()).limit(1))

async def get_next_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING, LotBase.id > current_lot_id).order_by(LotBase.id.asc()).limit(1))

async def get_previous_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING, LotBase.id < current_lot_id).order_by(LotBase.id.desc()).limit(1))

async def set_lot_applicant(lot_id: int, applicant: int):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id).with_for_update())
        lot.applicant = applicant
        await session.commit()

async def get_lot_applicant(lot_id: int):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id))
        return lot.applicant

async def set_new_lot_price(lot_id: int, bid: int):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id).with_for_update())
        lot.real_price += bid
        await session.commit()

async def set_message_id(lot_id: int, message_id: int):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id).with_for_update())
        lot.message_id = message_id
        await session.commit()

async def buy_now(lot_id, user_id, real_price: int):
    async with async_session() as session:
        lot = await session.scalar(select(LotBase).where(LotBase.id == lot_id).with_for_update())
        lot.status = LotStatus.SOLD
        lot.buyer = user_id
        lot.applicant = user_id
        lot.real_price = real_price
        await session.commit()

# ----------------- USER FUNCTIONS -----------------

async def get_user_data(tg_id: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(UserBase).where(UserBase.telegram_id == tg_id))

async def get_user_data_ref(ref_code: str):
    async with async_session() as session:
        referral = await session.scalar(select(ReferralBase).where(ReferralBase.link == ref_code))
        return await session.scalar(select(UserBase).where(UserBase.id == referral.user_id))


async def get_user_data_id(id: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(UserBase).where(UserBase.id == id))

async def get_user_by_username(username: str):
    async with async_session() as session:
        return await session.scalar(select(UserBase).where(UserBase.username == username))

async def set_new_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid))
        user.is_new = False
        await session.commit()

async def deposit_balance(tg_id: BigInteger, stars: int):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tg_id).with_for_update())
        user.balance += stars
        await session.commit()

async def increase_balance(tg_id: BigInteger, bid: int):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tg_id).with_for_update())
        user.balance += bid
        await session.commit()

async def decrease_balance(tg_id: BigInteger, bid: int):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tg_id).with_for_update())
        user.balance -= bid
        await session.commit()

async def ban_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid).with_for_update())
        user.is_banned = True
        await session.commit()

async def unban_user(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid).with_for_update())
        user.is_banned = False
        await session.commit()

async def warn_user(utid: BigInteger, atid: BigInteger, reason: str):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == utid).with_for_update())
        admin = await session.scalar(select(UserBase).where(UserBase.telegram_id == atid).with_for_update())
        session.add(WarnBase(user_id = user.id, admin_id = admin.id, reason=reason))
        await session.commit()

async def warn_count(tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid).with_for_update())
        count_result = await session.execute(
            select(func.count()).select_from(WarnBase).where(WarnBase.user_id == user.id)
        )
        warning_count = count_result.scalar_one()

        return warning_count


async def get_blocked_users():
    async with async_session() as session:
        users = await session.scalars(select(UserBase).where(UserBase.is_banned == True))
        return [{key: getattr(user, key) for key in user.__table__.columns.keys()} for user in users]

# ----------------- REFERRAL FUNCTIONS -----------------

async def add_new_referral_link(referral_link: str, tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid).with_for_update())
        session.add(ReferralBase(user_id=user.id, link=referral_link))
        await session.commit()

async def set_user_referral(referral_id: BigInteger, tid: BigInteger):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid).with_for_update())
        user.ref_id = referral_id
        await session.commit()

async def get_user_referral(user_id: int):
    async with async_session() as session:
        referral = await session.scalar(select(ReferralBase).where(ReferralBase.user_id == user_id))
        return referral
