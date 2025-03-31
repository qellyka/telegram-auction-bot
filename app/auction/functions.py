import asyncio
import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select

from app.db.engine import async_session
from app.db.models import LotBase, LotStatus, LotModStatus
import app.db.requests as rq
from config import CHANNEL_ID, status_mapping, BOT_ID, TEXTS


async def check_expired_lots(bot: Bot):
    async with async_session() as session:
        now = datetime.datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)

        expired_lots = await session.scalars(
            select(LotBase)
            .where(
                LotBase.status == LotStatus.TRADING,
                LotBase.is_post == LotModStatus.APPROVED,
                LotBase.expired_at < now
            )
        )

        tasks = []

        for lot in expired_lots:
            tasks.append(process_lot(lot, bot))

        if tasks:
            await asyncio.gather(*tasks)
            await session.commit()

async def process_lot(lot: LotBase, bot: Bot):
    winner = await rq.get_user_data(lot.applicant)
    seller = await rq.get_user_data(lot.seller)
    if winner:
        lot.status = LotStatus.SOLD
        lot.buyer = winner.telegram_id
        await bot.send_message(chat_id=winner.telegram_id,
                         text=TEXTS["you_win_lot"].format(
                             id=lot.id,
                             username=seller.username
                         ))
        await bot.send_message(chat_id=lot.seller,
                               text=TEXTS["seller_send_gift_msg"].format(
                                   id=lot.id,
                                   username=winner.username
                               ))
        await bot.edit_message_caption(
            chat_id=f"@{CHANNEL_ID}",
            message_id=lot.message_id,
            caption=TEXTS["sold_lot_caption"].format(
                starter_price=lot.starter_price,
                moment_buy_price=lot.moment_buy_price,
                seller=seller.name,
                status=status_mapping.get(lot.status.value, "None"),
                name=winner.name
            ),
            parse_mode="HTML",
        )

    else:
        lot.status = LotStatus.EXPIRED
        await bot.send_message(chat_id=lot.seller,
                               text=TEXTS["seller_expired_lot_msg"].format(
                                   id=lot.id
                               ))
        await bot.edit_message_caption(
            chat_id=f"@{CHANNEL_ID}",
            message_id=lot.message_id,
            caption=TEXTS["expired_lot_caption"].format(
                id=lot.id,
                starter_price=lot.starter_price,
                moment_buy_price=lot.moment_buy_price,
                name=seller.name,
                status=status_mapping.get(lot.status.value, "None")
            ),
            parse_mode="HTML",
        )

async def background_tasks(bot: Bot):
    while True:
        await check_expired_lots(bot)
        await asyncio.sleep(60)

