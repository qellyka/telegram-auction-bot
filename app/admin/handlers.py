import asyncio

from aiogram import F, Router, types

import re

from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from app.middlewares import UserDBCheckMiddleware

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.db.requests as rq

from app.filters import IsAdmin, IsAdminCb

import app.admin.keyboards as kb

from config import CHANNEL_ID, BOT_ID, status_mapping, TEXTS

admin_router = Router()

admin_router.message.outer_middleware(UserDBCheckMiddleware())

class ManageUser(StatesGroup):
    username = State()

@admin_router.message(IsAdmin(), Command("menu"))
async def menu(message: Message):
    await message.answer(text=TEXTS["main_menu_msg"],
                         reply_markup=kb.admin_menu)

@admin_router.message(IsAdmin(), F.text == "🛠️Вопросы пользователей")
async def tech_channel(message: Message):
    await message.answer(text=TEXTS["tech_channel_msg"],
                         reply_markup=kb.tech_channel_menu)

@admin_router.message(IsAdmin(), F.text == "🃏Черный список")
async def view_black_list(message: Message):
    users = await rq.get_blocked_users()
    if users:
        await message.answer(text=TEXTS["banned_list_msg"])
        for user in users:
            await message.answer(f"{user['username']}")
    else:
        await message.answer(text=TEXTS["banned_list_msg_empty_msg"])

@admin_router.message(IsAdmin(), F.text == "🪪Управление пользователями")
async def manage_users(message: Message, state: FSMContext):
    await state.set_state(ManageUser.username)
    await message.answer(text=TEXTS["send_user_username_msg"],
                         reply_markup=kb.interrupt_work)

@admin_router.message(IsAdmin(), ManageUser.username)
async def manage_users_state(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    user = await rq.get_user_by_username(data["username"])
    if user and not(user.is_admin):
        if user.is_banned:
            await message.answer(text=TEXTS["user_profile_msg"].format(
                                 username=user.username,
                                 lots=user.lots,
                                 balance=user.balance
            ),
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                [InlineKeyboardButton(text="Разбанить пользователя",
                                                                      callback_data=f"unban_user_{user.telegram_id}")],
                                                [InlineKeyboardButton(text="Посмотреть лоты пользователя",
                                                                      callback_data=f"user_lots_{user.telegram_id}")],
                                                [InlineKeyboardButton(text="Написать пользователю",
                                                                      url=f"tg://user?id={user.telegram_id}")],
                                 ])
                                 )
            await state.clear()
        else:
            await message.answer(text=TEXTS["user_profile_msg"].format(
                                 username=user.username,
                                 lots=user.lots,
                                 balance=user.balance
            ),
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text="Забанить пользователя",
                                                           callback_data=f"ban_user_{user.telegram_id}")],
                                     [InlineKeyboardButton(text="Посмотреть лоты пользователя",
                                                           callback_data=f"user_lots_{user.telegram_id}")],
                                     [InlineKeyboardButton(text="Написать пользователю",
                                                           url=f"tg://user?id={user.telegram_id}")],
                                 ])
                                 )
            await state.clear()
    elif user and user.is_admin:
        await message.answer(TEXTS["cant_see_admin_account_msg"])
    else:
        await message.answer(TEXTS["user_not_found"])


@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^ban_user_\d+$", cb.data))
async def ban_user(cb: CallbackQuery):
    tg_id = int(cb.data.split("_")[-1])
    await rq.ban_user(tid=tg_id)
    await cb.message.edit_text(TEXTS["successful_ban_msg"])
    await cb.bot.send_message(chat_id=tg_id,
                              text=TEXTS["send_ban_msg"],
                              reply_markup=kb.tech_bot_menu)

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^unban_user_\d+$", cb.data))
async def ban_user(cb: CallbackQuery):
    tg_id = int(cb.data.split("_")[-1])
    await rq.unban_user(tid=tg_id)
    await cb.message.edit_text(TEXTS["successful_unban_msg"])
    await cb.bot.send_message(chat_id=tg_id,
                              text=TEXTS["send_unban_msg"])


@admin_router.message(IsAdmin(), F.text == "🎫Посмотреть новые лоты")
async def new_lots_menu(message: Message):
    lot = await rq.get_first_new_lot()
    if lot:
        seller = await rq.get_user_data(lot.seller)
        await message.answer_photo(photo=lot.photo_id,
                                   caption=TEXTS["see_new_lots_caption"].format(
                                       id=lot.id,
                                       starter_price=lot.starter_price,
                                       real_price=lot.real_price,
                                       min_next_price=lot.real_price + 1,
                                       moment_buy_price=lot.moment_buy_price,
                                       name=seller.name,
                                       expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M')
                                   ),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                    [InlineKeyboardButton(text="✅ Одобрить",
                                                                          callback_data=f"approve_lot_{lot.id}")],
                                                    [InlineKeyboardButton(text="❌ Отклонить",
                                                                          callback_data=f"reject_lot_{lot.id}")],
                                                    [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                                                          callback_data=f"prev_lot_{lot.id}"),
                                                     InlineKeyboardButton(text="⏭️ Следующий лот",
                                                                          callback_data=f"next_lot_{lot.id}")],
                                                    [InlineKeyboardButton(text="🔚 Завершить модерирование",
                                                    callback_data="end_moderation")]]),
                                   parse_mode="HTML")
    else:
        await message.answer("🙅 Новых лотов сейчас нет.")

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^approve_lot_\d+$", cb.data))
async def approve_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    await rq.approve_lot(lot_id=lot_id)
    lot = await rq.get_lot_data(lot_id=lot_id)
    user = await rq.get_user_data_id(lot.user_id)
    seller = await rq.get_user_data(lot.seller)
    message = await cb.bot.send_photo(chat_id=f"@{CHANNEL_ID}",
                                      photo=lot.photo_id,
                                      caption=TEXTS["send_new_lot_caption"].format(
                                          id=lot.id,
                                          starter_price=lot.starter_price,
                                          real_price=lot.real_price,
                                          min_next_price=lot.real_price + 1,
                                          moment_buy_price=lot.moment_buy_price,
                                          name=seller.name,
                                          expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                          status=status_mapping.get(lot.status.value)
                                      ),
                                      parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                          [InlineKeyboardButton(text="Участвовать в аукционе",
                                                                url=f"https://t.me/{BOT_ID}?start={lot.uuid}")]
                                      ])
                            )
    await cb.answer("Лот #" + str(lot_id) + " одобрен.")
    await cb.bot.send_message(chat_id=user.telegram_id,
                                        text=TEXTS["send_approve_lot_notif"].format(
                                            CHANNEL_ID=CHANNEL_ID,
                                            message_id=message.message_id
                                        ))
    await rq.set_message_id(lot_id, message.message_id)
    next_lot = await rq.get_next_lot(lot_id)
    if next_lot:
        nx_seller = await rq.get_user_data(next_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=TEXTS["send_new_lot_caption"].format(
                                          id=next_lot.id,
                                          starter_price=next_lot.starter_price,
                                          real_price=next_lot.real_price,
                                          min_next_price=next_lot.real_price + 1,
                                          moment_buy_price=next_lot.moment_buy_price,
                                          name=nx_seller.name,
                                          expired_at=next_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                          status=status_mapping.get(next_lot.status.value)
                                      ),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить",
                                  callback_data=f"approve_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="❌ Отклонить",
                                  callback_data=f"reject_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_{next_lot.id}"),
             InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить модерирование",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.message.delete()
        msg = await cb.message.answer(TEXTS["no_new_lots_msg"])
        await asyncio.sleep(3)
        await msg.delete()

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^reject_lot_\d+$", cb.data))
async def reject_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id=lot_id)
    user = await rq.get_user_data_id(lot.user_id)
    await rq.reject_lot(lot_id=lot_id)
    await cb.answer("Лот №" + str(lot_id) + " отклонен.")
    await cb.bot.send_message(chat_id=user.telegram_id,
                              text=TEXTS["send_reject_lot_notif"].format(
                                  id=lot.id
                              ),
                              reply_markup=kb.tech_bot_menu)
    next_lot = await rq.get_next_lot(lot_id)
    if next_lot:
        nx_seller = await rq.get_user_data(next_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=TEXTS["send_new_lot_caption"].format(
                                          id=next_lot.id,
                                          starter_price=next_lot.starter_price,
                                          real_price=next_lot.real_price,
                                          min_next_price=next_lot.real_price + 1,
                                          moment_buy_price=next_lot.moment_buy_price,
                                          name=nx_seller.name,
                                          expired_at=next_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                          status=status_mapping.get(next_lot.status.value)
                                      ),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить",
                                  callback_data=f"approve_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="❌ Отклонить",
                                  callback_data=f"reject_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_{next_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить модерирование",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        msg = await cb.message.edit_text(TEXTS["no_new_lots_msg"])
        await asyncio.sleep(3)
        await msg.delete()

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^next_lot_\d+$", cb.data))
async def reject_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    next_lot = await rq.get_next_lot(lot_id)
    if next_lot:
        nx_seller = await rq.get_user_data(next_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=TEXTS["send_new_lot_caption"].format(
                                          id=next_lot.id,
                                          starter_price=next_lot.starter_price,
                                          real_price=next_lot.real_price,
                                          min_next_price=next_lot.real_price + 1,
                                          moment_buy_price=next_lot.moment_buy_price,
                                          name=nx_seller.name,
                                          expired_at=next_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                          status=status_mapping.get(next_lot.status.value)
                                      ),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить",
                                  callback_data=f"approve_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="❌ Отклонить",
                                  callback_data=f"reject_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_{next_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить модерирование",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.answer(TEXTS["reviewed_all_lots_after_this_msg"])

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^prev_lot_\d+$", cb.data))
async def reject_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    prev_lot = await rq.get_previous_lot(lot_id)
    if prev_lot:
        prev_seller = await rq.get_user_data(prev_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=prev_lot.photo_id,
            caption=TEXTS["send_new_lot_caption"].format(
                                          id=prev_lot.id,
                                          starter_price=prev_lot.starter_price,
                                          real_price=prev_lot.real_price,
                                          min_next_price=prev_lot.real_price + 1,
                                          moment_buy_price=prev_lot.moment_buy_price,
                                          name=prev_seller.name,
                                          expired_at=prev_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                          status=status_mapping.get(prev_lot.status.value)
                                      ),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить",
                                  callback_data=f"approve_lot_{prev_lot.id}")],
            [InlineKeyboardButton(text="❌ Отклонить",
                                  callback_data=f"reject_lot_{prev_lot.id}")],
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_{prev_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_{prev_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить модерирование",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.answer(TEXTS["reviewed_all_lots_before_this_msg"])

@admin_router.callback_query(IsAdminCb(), F.data == "end_moderation")
async def end_moderation(cb: CallbackQuery):
    await cb.message.delete()
    msg = await cb.message.answer(TEXTS["end_moderation_msg"])
    await asyncio.sleep(5)
    await msg.delete()

@admin_router.callback_query(IsAdminCb(), F.data == "interrupt_work")
async def interrupt_work(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await state.clear()
    new_message = await cb.message.answer(TEXTS["interrupt_work_msg"])
    await asyncio.sleep(5)
    await new_message.delete()
