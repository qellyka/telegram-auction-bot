import datetime
import enum

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey, BigInteger, Boolean, false
from typing import Optional

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Status(enum.Enum):
    bidding = "bidding"
    sold_out = "sold_out"
    time_over = "time_over"

class UserBase(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
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
    completion_time: Mapped[datetime.datetime]
    buyer: Mapped[Optional[str]]
    seller: Mapped[str]
    is_post: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    status: Mapped[Status]
