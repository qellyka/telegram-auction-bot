import datetime
import enum

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey, BigInteger, Boolean
from typing import Optional

class Base(AsyncAttrs, DeclarativeBase):
    pass

class LotStatus(enum.Enum):
    TRADING = "TRADING"
    SOLD = "SOLD"
    EXPIRED = "EXPIRED"

class LotModStatus(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class UserBase(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[Optional[str]]
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str]
    balance: Mapped[int] = mapped_column(default=0)
    lots: Mapped[int] = mapped_column(default=0)
    ref_code: Mapped[Optional[str]]
    warns: Mapped[int] = mapped_column(default=0)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"

class LotBase(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str]
    user_id: Mapped[int] = mapped_column(BigInteger ,ForeignKey("users.id", ondelete="CASCADE"))
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
