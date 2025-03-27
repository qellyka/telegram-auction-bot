import asyncio
import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from sqlalchemy import select

from app.db.engine import async_session
from app.db.models import LotBase, LotStatus, LotModStatus
import app.db.requests as rq
from config import CHANNEL_ID, status_mapping, BOT_ID


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
                         text=f"Ваша ставка на лот #{lot.id} победила. В течение часа @{seller.username} должен отправить вам подарок, "
                              f"если этого не случилось откройте спор.")
        await bot.send_message(chat_id=lot.seller,
                               text=f'Ваш лот #{lot.id} закончился. В нем есть победитель @{winner.username}. В течение часа вы должны отправить подарок, '
                                    f'если вы этого не сделаете покупатель может открыть спор и вернуть звезды, а вас забанят!')
        await bot.edit_message_caption(
            chat_id=f"@{CHANNEL_ID}",
            message_id=lot.message_id,
            caption=f"Лот: <b>#{lot.id}</b>\n"
                    f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                    f"Последняя ставка: <b>{lot.real_price}</b>🌟\n"
                    f"Продвец: <b>{seller.name}</b>\n"
                    f"Статус: <b>{status_mapping.get(lot.status.value, "None")}</b>\n"
                    f"Покупатель: <b>{winner.name}</b>",
            parse_mode="HTML",
        )

    else:
        lot.status = LotStatus.EXPIRED
        await bot.send_message(chat_id=lot.seller,
                               text=f'Ваш лот #{lot.id} закончился. На него никто не сделал ставки.')
        await bot.edit_message_caption(
            chat_id=f"@{CHANNEL_ID}",
            message_id=lot.message_id,
            caption=f"Лот: <b>#{lot.id}</b>\n"
                    f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                    f"Цена моментальной покупки: <b>{lot.moment_buy_price}</b>🌟\n"
                    f"Продвец: <b>{seller.name}</b>\n"
                    f"Статус: <b>{status_mapping.get(lot.status.value, "None")}</b>\n",
            parse_mode="HTML",
        )

async def background_tasks(bot: Bot):
    """Запускает периодическую проверку лотов"""
    while True:
        await check_expired_lots(bot)
        await asyncio.sleep(60)

