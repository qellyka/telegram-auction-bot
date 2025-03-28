from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from app.db.models import LotStatus
import app.db.requests as rq

from config import BOT_ID, CHANNEL_ID, status_mapping

import app.user.keyboards as kb

async def bid_lot(lot, bid: int, cb: CallbackQuery, lot_id: int, user_id: int):
    lot_seller = await rq.get_user_data_id(lot.user_id)
    user = await rq.get_user_data(user_id)

    if lot.status == LotStatus.SOLD:
        await cb.answer()
        await cb.message.delete()
        await cb.message.answer("Лот уже выкуплен.")
        return

    elif lot.status == LotStatus.EXPIRED:
        await cb.answer()
        await cb.message.delete()
        await cb.message.answer("Лот был закрыт по времени, его никто не купил.")
        return

    elif lot_seller.telegram_id == user_id:
        await cb.answer()
        await cb.message.answer("Вы не можете делать ставки на свой собственный лот.")
        return

    elif user.balance < lot.real_price + bid:
        await cb.answer()
        await cb.message.answer("💰На вашем балансе недостаточно звезд⭐, пополните баланс, нажав на кнопку ниже ⬇️",
                                reply_markup=kb.profile_menu)
        return

    applicant = await rq.get_lot_applicant(lot_id)

    if applicant == user_id:
        await cb.answer()
        await cb.message.answer("⌛️Вы уже сделали ставку на этот лот, дождитесь пока её перебьют  или купите мгновенно⌛️")
        return

    if applicant and applicant != user_id:
        await cb.bot.send_message(
         chat_id=applicant,
         text=f"Ваша ставка на лот #{lot.id} была перебита❗️Средства возвращены на баланс💰"
        )
        await rq.increase_balance(applicant, lot.real_price)

    await rq.set_lot_applicant(lot_id, user_id)
    await rq.set_new_lot_price(lot_id, bid)

    lot = await rq.get_lot_data(lot_id)
    await cb.answer()
    await rq.decrease_balance(user_id, lot.real_price)
    await cb.message.answer("Вы успешно сделали ставку!")
    await cb.bot.edit_message_caption(
        chat_id=f"@{CHANNEL_ID}",
        message_id=lot.message_id,
        caption=f"Лот: <b>#{lot.id}</b>\n"
                f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                f"Последняя ставка: <b>{lot.real_price}</b>🌟\n"
                f"Следующая минимальная ставка: <b>{lot.real_price + 1}</b>🌟\n"
                f"Цена моментальной покупки: <b>{lot.moment_buy_price}</b>🌟\n"
                f"Продвец: <b>{lot_seller.name}</b>\n"
                f"Время окончания: <b>{lot.expired_at.strftime('%d.%m.%Y %H:%M')}</b> (MSK)\n"
                f"Статус: <b>{status_mapping.get(lot.status.value, "None")}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
         inline_keyboard=[
             [InlineKeyboardButton(
                 text="Принять участие",
                 url=f"https://t.me/{BOT_ID}?start={lot.uuid}"
             )]
         ]
        )
    )