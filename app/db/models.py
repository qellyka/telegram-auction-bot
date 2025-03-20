import datetime
import enum

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey, BigInteger, Boolean, false, true
from typing import Optional

class Base(AsyncAttrs, DeclarativeBase):
    pass

class LotStatus(enum.Enum):
    TRADING = "TRADING"       # Идут торги
    SOLD = "SOLD"             # Продан
    EXPIRED = "EXPIRED"

class LotModStatus(enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"

class UserBase(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str]
    balance: Mapped[int] = mapped_column(default=0)
    lots: Mapped[int] = mapped_column(default=0)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"

class LotBase(Base):
    __tablename__ = 'lots'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger ,ForeignKey('users.id', ondelete="CASCADE"))
    photo_id: Mapped[str]
    starter_price: Mapped[int]
    real_price: Mapped[int]
    moment_buy_price: Mapped[Optional[int]]
    expired_at: Mapped[datetime.datetime]
    expired_time: Mapped[int]
    buyer: Mapped[Optional[str]]
    seller: Mapped[str]
    is_post: Mapped[LotModStatus]
    status: Mapped[LotStatus]
