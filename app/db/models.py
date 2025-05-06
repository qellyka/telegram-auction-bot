import datetime
import enum

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, BigInteger, Boolean
from typing import Optional

class Base(AsyncAttrs, DeclarativeBase):
    pass

# ----------------- ENUMS -----------------

class LotStatus(enum.Enum):
    TRADING = "TRADING"
    SOLD = "SOLD"
    EXPIRED = "EXPIRED"

class LotModStatus(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class BlankModStatus(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class BankEnum(enum.Enum):
    TINKOFF = "TINKOFF"
    SBER = "SBER"
    ALFA = "ALFA"
    STAR = "STAR"

class ResultEnum(enum.Enum):
    CONFIRM = "CONFIRM"
    DECLINE = "DECLINE"

class DisputeStatusEnum(enum.Enum):
    CHECK = "CHECK"
    UNCHECK = "UNCHECK"


# ----------------- USERS -----------------

class UserBase(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str]
    name: Mapped[Optional[str]]
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_withdrawer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    balance: Mapped[int] = mapped_column(default=0)
    lots: Mapped[int] = mapped_column(default=0)
    ref_id: Mapped[Optional[int]] = mapped_column(BigInteger)

# ----------------- REFERRALS -----------------

class ReferralBase(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    link: Mapped[Optional[str]]
    percent: Mapped[int] = mapped_column(default=5)

# ----------------- WARNS -----------------

class WarnBase(Base):
    __tablename__ = "warns"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[Optional[str]]
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

# ----------------- LOTS -----------------

class LotBase(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    photo_id: Mapped[str]
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    starter_price: Mapped[int]
    real_price: Mapped[int]
    moment_buy_price: Mapped[Optional[int]]
    expired_at: Mapped[datetime.datetime]
    expired_time: Mapped[int]
    buyer: Mapped[Optional[int]] = mapped_column(BigInteger)
    applicant: Mapped[Optional[int]] = mapped_column(BigInteger)
    seller: Mapped[int] = mapped_column(BigInteger)
    is_post: Mapped[LotModStatus]
    status: Mapped[LotStatus]

# ----------------- WITHDRAWAL -----------------

class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    bank: Mapped[BankEnum]
    account_number: Mapped[str]
    star_amount: Mapped[int]
    receipt_id: Mapped[Optional[str]]
    created_at: Mapped[datetime.datetime]
    processed_at: Mapped[Optional[datetime.datetime]]
    status: Mapped[BlankModStatus]

class DisputeBase(Base):
    __tablename__ = "disputes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id"))
    seller_msg_id: Mapped[int]
    user_msg_id: Mapped[int]
    created_at: Mapped[datetime.datetime]
    processed_at: Mapped[Optional[datetime.datetime]]
    result: Mapped[Optional[ResultEnum]]
    status: Mapped[BlankModStatus]

