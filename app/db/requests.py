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
    WarnBase,
    WithdrawalRequest,
    BankEnum,
    BlankModStatus
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

async def get_first_new_lot():
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING).order_by(LotBase.id.asc()).limit(1))

async def get_next_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING, LotBase.id > current_lot_id).order_by(LotBase.id.asc()).limit(1))

async def get_previous_lot(current_lot_id):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.is_post == LotModStatus.PENDING, LotBase.id < current_lot_id).order_by(LotBase.id.desc()).limit(1))

async def get_first_user_lot(tid: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.seller == tid).order_by(LotBase.id.asc()).limit(1))

async def get_next_user_lot(current_lot_id, tid: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.seller == tid, LotBase.id > current_lot_id).order_by(LotBase.id.asc()).limit(1))

async def get_previous_user_lot(current_lot_id, tid: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.seller == tid, LotBase.id < current_lot_id).order_by(LotBase.id.desc()).limit(1))

async def get_first_user_lot_bid(tid: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.applicant == tid, LotBase.status == LotStatus.TRADING).order_by(LotBase.id.asc()).limit(1))

async def get_next_user_lot_bid(current_lot_id, tid: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.applicant == tid, LotBase.id > current_lot_id, LotBase.status == LotStatus.TRADING).order_by(LotBase.id.asc()).limit(1))

async def get_previous_user_lot_bid(current_lot_id, tid: BigInteger):
    async with async_session() as session:
        return await session.scalar(select(LotBase).where(LotBase.applicant == tid, LotBase.id < current_lot_id, LotBase.status == LotStatus.TRADING).order_by(LotBase.id.desc()).limit(1))

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
        if referral is None:
            print("Referral is not found")
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
        if bid <=2000000:
            user.balance += bid
        else:
            print("Value of bid too high")
        await session.commit()

async def decrease_balance(tg_id: BigInteger, bid: int):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tg_id).with_for_update())
        if bid <= 2000000:
            user.balance -= bid
        else:
            print("Value of bid too high")
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

async def notify_admins(message: str, bot):
    async with async_session() as session:
        admins = await session.scalars(
            select(UserBase).where(UserBase.is_withdrawer == True)
        )
        for admin in admins:
            try:
                await bot.send_message(admin.telegram_id, message)
            except Exception as e:
                print(f"Не удалось отправить сообщение {admin.telegram_id}: {e}")

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

# ----------------- WITHDRAWAL BLANKS -----------------

async def get_blank_data(bid: int):
    async with async_session() as session:
        return await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.id == bid))

async def add_new_blank(tid: BigInteger ,stars: int, bank: str, number: str):
    async with async_session() as session:
        user = await session.scalar(select(UserBase).where(UserBase.telegram_id == tid).with_for_update())
        if bank == "tinkoff":
            session.add(WithdrawalRequest(user_id=user.id,
                                          bank=BankEnum.TINKOFF,
                                          account_number=number,
                                          star_amount=stars,
                                          status=BlankModStatus.PENDING,
                                          created_at=datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)))
        elif bank == "sberbank":
            session.add(WithdrawalRequest(user_id=user.id,
                                          bank=BankEnum.SBER,
                                          account_number=number,
                                          star_amount=stars,
                                          status=BlankModStatus.PENDING,
                                          created_at=datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)))
        elif bank == "alfabank":
            session.add(WithdrawalRequest(user_id=user.id,
                                          bank=BankEnum.ALFA,
                                          account_number=number,
                                          star_amount=stars,
                                          status=BlankModStatus.PENDING,
                                          created_at=datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)))
        elif bank == "stars":
            session.add(WithdrawalRequest(user_id=user.id,
                                          bank=BankEnum.STAR,
                                          account_number=number,
                                          star_amount=stars,
                                          status=BlankModStatus.PENDING,
                                          created_at=datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)))
        await session.commit()

async def get_first_new_blank():
    async with async_session() as session:
        return await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.status == BlankModStatus.PENDING).order_by(WithdrawalRequest.id.asc()).limit(1))

async def get_next_blank(current_blank_id):
    async with async_session() as session:
        return await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.status == BlankModStatus.PENDING, WithdrawalRequest.id > current_blank_id).order_by(WithdrawalRequest.id.asc()).limit(1))

async def get_previous_blank(current_blank_id):
    async with async_session() as session:
        return await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.status == BlankModStatus.PENDING, WithdrawalRequest.id < current_blank_id).order_by(WithdrawalRequest.id.desc()).limit(1))

async def approve_blank(photo_id: str, admin_id: BigInteger, blank_id: int):
    async with async_session() as session:
        blank = await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.id == blank_id))
        admin = await session.scalar(select(UserBase).where(UserBase.telegram_id == admin_id))
        blank.admin_id = admin.id
        blank.receipt_id = photo_id
        blank.processed_at = datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
        blank.status = BlankModStatus.APPROVED
        await session.commit()

async def reject_blank(admin_id: BigInteger, blank_id: int):
    async with async_session() as session:
        blank = await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.id == blank_id))
        admin = await session.scalar(select(UserBase).where(UserBase.telegram_id == admin_id))
        blank.admin_id = admin.id
        blank.receipt_id = None
        blank.processed_at = datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
        blank.status = BlankModStatus.REJECTED
        await session.commit()
