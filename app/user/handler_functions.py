from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from app.db.models import LotStatus
import app.db.requests as rq

from config import BOT_ID, CHANNEL_ID, status_mapping, TEXTS

import app.user.keyboards as kb

async def bid_lot(lot, bid: int, cb: CallbackQuery, lot_id: int, user_id: int):
    seller = await rq.get_user_data_id(lot.user_id)
    user = await rq.get_user_data(user_id)

    if lot.status == LotStatus.SOLD:
        await cb.answer()
        await cb.message.delete()
        await cb.message.answer(TEXTS["lot_sold_msg"])
        return

    elif lot.status == LotStatus.EXPIRED:
        await cb.answer()
        await cb.message.delete()
        await cb.message.answer(TEXTS["lot_expired_msg"])
        return

    elif seller.telegram_id == user_id:
        await cb.answer()
        await cb.message.answer(TEXTS["you_are_seller_msg"])
        return

    elif user.balance < lot.real_price + bid:
        await cb.answer()
        await cb.message.answer(text=TEXTS["not_enough_stars"],
                                reply_markup=kb.profile_menu)
        return

    applicant = await rq.get_lot_applicant(lot_id)

    if applicant == user_id:
        await cb.answer()
        await cb.message.answer(TEXTS["bet_is_already_yours_msg"])
        return

    if applicant and applicant != user_id:
        await cb.bot.send_message(
         chat_id=applicant,
         text=TEXTS["bid_exceeded_msg"].format(
             id=lot.id
         )
        )
        await rq.increase_balance(applicant, lot.real_price)

    await rq.set_lot_applicant(lot_id, user_id)
    await rq.set_new_lot_price(lot_id, bid)

    lot = await rq.get_lot_data(lot_id)
    await cb.answer()
    await rq.decrease_balance(user_id, lot.real_price)
    await cb.message.answer(TEXTS["successful_bid_msg"])
    await cb.bot.edit_message_caption(
        chat_id=f"@{CHANNEL_ID}",
        message_id=lot.message_id,
        caption=TEXTS["update_lot_after_bid_caption"].format(
            id=lot.id,
            starter_price=lot.starter_price,
            real_price=lot.real_price,
            min_next_price=lot.real_price + 1,
            moment_buy_price=lot.moment_buy_price,
            name=seller.name,
            expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M'),
            status=status_mapping.get(lot.status.value, "None")
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
         inline_keyboard=[
             [InlineKeyboardButton(
                 text="Участвовать в аукционе",
                 url=f"https://t.me/{BOT_ID}?start={lot.uuid}"
             )]
         ]
        )
    )