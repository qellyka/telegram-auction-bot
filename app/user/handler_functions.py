from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy import BigInteger

from app.db.models import LotStatus
import app.db.requests as rq
from config import BOT_ID, CHANNEL_ID, status_mapping

# @user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_10_\d+$", cb.data))
# async def outbid_bid_1(cb: CallbackQuery):
#     lot_id = int(cb.data.split("_")[-1])
#     lot = await rq.get_lot_data(lot_id)

async def bid_lot(lot, bid: int, cb: CallbackQuery, lot_id: int, user_id: BigInteger):
    if lot.status == LotStatus.SOLD:
        await cb.message.delete()
        await cb.message.answer("Лот уже выкуплен.")
    elif lot.status == LotStatus.EXPIRED:
        await cb.message.delete()
        await cb.message.answer("Лот был закрыт по времени, его никто не купил.")
    else:
        applicant = await rq.get_lot_applicant(lot_id)
        if applicant:
            applicant = await rq.get_lot_applicant(lot_id)
            await cb.bot.send_message(chat_id=applicant,
                                      text=f"Внимание! Ваша ставка на лот #{lot.id} была перебита.(Тут будет кнопка чтобы перебить в ответ)")
            await rq.set_lot_applicant(lot_id, user_id)
            await rq.set_new_lot_price(lot_id, bid)
            lot = await rq.get_lot_data(lot_id)
            await cb.message.answer("Вы успешно перебили ставку!")
            await cb.bot.edit_message_caption(chat_id=f"@{CHANNEL_ID}",
                                              message_id=lot.message_id,
                                              caption=f"Лот: <b>#{lot.id}</b>\n"
                                                      f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                                                      f"Последняя ставка: <b>{lot.real_price}</b>🌟\n"
                                                      f"Следующая минимальная ставка: <b>{lot.real_price + 1}</b>🌟\n"
                                                      f"Цена моментальной покупки: <b>{lot.moment_buy_price}</b>🌟\n"
                                                      f"Продвец: <b>{lot.seller}</b>\n"
                                                      f"Время окончания: <b>{lot.expired_at.strftime('%Y-%m-%d %H:%M:%S')}</b> (MSK)\n"
                                                      f"Статус: {status_mapping.get(lot.status.value)}",
                                              parse_mode="HTML",
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                    [InlineKeyboardButton(text="Принять участие",
                                                                          url=f"https://t.me/{BOT_ID}?start={lot.uuid}")]
                                      ]))
        else:
            await rq.set_lot_applicant(lot_id, user_id)
            await rq.set_new_lot_price(lot_id, bid)
            lot = await rq.get_lot_data(lot_id)
            await cb.message.answer("Вы успешно сделали ставку!")
            await cb.bot.edit_message_caption(chat_id=f"@{CHANNEL_ID}",
                                              message_id=lot.message_id,
                                              caption=f"Лот: <b>#{lot.id}</b>\n"
                                                      f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                                                      f"Последняя ставка: <b>{lot.real_price}</b>🌟\n"
                                                      f"Следующая минимальная ставка: <b>{lot.real_price + 1}</b>🌟\n"
                                                      f"Цена моментальной покупки: <b>{lot.moment_buy_price}</b>🌟\n"
                                                      f"Продвец: <b>{lot.seller}</b>\n"
                                                      f"Время окончания: <b>{lot.expired_at.strftime('%Y-%m-%d %H:%M:%S')}</b> (MSK)\n"
                                                      f"Статус: {status_mapping.get(lot.status.value)}",
                                              parse_mode="HTML",
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                    [InlineKeyboardButton(text="Принять участие",
                                                                          url=f"https://t.me/{BOT_ID}?start={lot.uuid}")]
                                      ]))