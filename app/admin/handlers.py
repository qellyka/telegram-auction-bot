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

from config import CHANNEL_ID, BOT_ID, status_mapping

admin_router = Router()

admin_router.message.outer_middleware(UserDBCheckMiddleware())

class ManageUser(StatesGroup):
    username = State()

@admin_router.message(IsAdmin(), Command("menu"))
async def menu(message: Message):
    await message.answer("Выберите, что вы  хотите сделать в меню. 🛠", reply_markup=kb.admin_menu)

@admin_router.message(IsAdmin(), F.text == "🛠️Вопросы пользователей")
async def tech_channel(message: Message):
    await message.answer(text="⁉️Перейдите в чат тех поддержки, для того, чтобы посмотреть вопросы других пользователей⁉️",
                         reply_markup=kb.tech_channel_menu)

@admin_router.message(IsAdmin(), F.text == "🃏Черный список")
async def view_black_list(message: Message):
    users = await rq.get_blocked_users()
    if users:
        await message.answer(text="Список забаненых пользователей: ")
        for user in users:
            await message.answer(f"{user['username']}")
    else:
        await message.answer(text="Список пуст.")

@admin_router.message(IsAdmin(), F.text == "🪪Управление пользователями")
async def manage_users(message: Message, state: FSMContext):
    await state.set_state(ManageUser.username)
    await message.answer("🧑‍💻 Введите username пользователя (без @).",
                         reply_markup=kb.interrupt_work)

@admin_router.message(IsAdmin(), ManageUser.username)
async def manage_users_state(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    user = await rq.get_user_by_username(data["username"])
    if user and not(user.is_admin):
        if user.is_banned:
            await message.answer(text=f"👤 Имя пользователя:  {user.username} \n"
                                      f"📍 Количество лотов:  {user.lots} \n"
                                      f"💰 Баланс пользователя:  {user.balance}⭐ \n",
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
            await message.answer(text=f"👤 Имя пользователя:  {user.username} \n"
                                      f"📍 Количество лотов:  {user.lots} \n"
                                      f"💰 Баланс пользователя:  {user.balance}⭐ \n",
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
        await message.answer("❌ Вы не можете просматривать профили администраторов ❌")
    else:
        await message.answer("❌ Пользователь  не был найден ❌")


@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^ban_user_\d+$", cb.data))
async def ban_user(cb: CallbackQuery):
    tg_id = int(cb.data.split("_")[-1])
    await rq.ban_user(tid=tg_id)
    await cb.message.edit_text("Пользователь успешно забанен.")
    await cb.bot.send_message(chat_id=tg_id,
                              text="🚫 Вы были забанены 🚫 \nЕсли это произошло по ошибке, то обратитесь в тех поддержку.❗️",
                              reply_markup=kb.tech_bot_menu)

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^unban_user_\d+$", cb.data))
async def ban_user(cb: CallbackQuery):
    tg_id = int(cb.data.split("_")[-1])
    await rq.unban_user(tid=tg_id)
    await cb.message.edit_text("Пользователь успешно разбанен.")
    await cb.bot.send_message(chat_id=tg_id,
                              text="❗️Вы были разабнены❗️\n⚠️ Повторные нарушения могут привести к бану навсегда! Советуем соблюдать правила. ")


@admin_router.message(IsAdmin(), F.text == "🎫Посмотреть новые лоты")
async def new_lots_menu(message: Message):
    lot = await rq.get_first_new_lot()
    if lot:
        seller = await rq.get_user_data(lot.seller)
        await message.answer_photo(photo=lot.photo_id,
                                   caption=f"Лот: <b>#{lot.id}</b>\n"
                                           f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                                           f"Последняя ставка: <b>{lot.real_price}</b>🌟\n"
                                           f"Следующая минимальная ставка: <b>{lot.real_price + 1}</b>🌟\n"
                                           f"Цена моментальной покупки: <b>{lot.moment_buy_price}</b>🌟\n"
                                           f"Продвец: <b>{seller.name}</b>\n"
                                           f"Время окончания: <b>{lot.expired_at.strftime('%d.%m.%Y %H:%M')}</b> (MSK)\n",
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
                                      caption=f"Лот: <b>#{lot.id}</b>\n"
                                              f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                                              f"Следующая минимальная ставка: <b>{lot.real_price + 1}</b>🌟\n"
                                              f"Цена моментальной покупки: <b>{lot.moment_buy_price}</b>🌟\n"
                                              f"Продвец: <b>{seller.name}</b>\n"
                                              f"Время окончания: <b>{lot.expired_at.strftime('%d.%m.%Y %H:%M')}</b> (MSK)\n"
                                              f"Статус: <b>{status_mapping.get(lot.status.value)}</b>",
                                      parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                          [InlineKeyboardButton(text="Принять участие",
                                                                url=f"https://t.me/{BOT_ID}?start={lot.uuid}")]
                                      ])
                            )
    await cb.answer("Лот #" + str(lot_id) + " одобрен.")
    await cb.bot.send_message(chat_id=user.telegram_id,
                                        text=f"✅ Ваш лот был одобрен и выставлен на продажу.\n"
                                             f"🔗 Ссылка на ваш лот : https://t.me/{CHANNEL_ID}/{message.message_id}")
    await rq.set_message_id(lot_id, message.message_id)
    next_lot = await rq.get_next_lot(lot_id)
    if next_lot:
        nx_user = await rq.get_user_data(next_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=f"Лот: <b>#{next_lot.id}</b>\n"
                    f"Стартовая цена: <b>{next_lot.starter_price}</b>🌟\n"
                    f"Следующая минимальная ставка: <b>{next_lot.real_price + 1}</b>🌟\n"
                    f"Цена моментальной покупки: <b>{next_lot.moment_buy_price}</b>🌟\n"
                    f"Продвец: <b>{nx_user.name}</b>\n"
                    f"Время окончания: <b>{next_lot.expired_at.strftime('%Y-%m-%d %H:%M:%S')}</b> (MSK)\n",
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
        msg = await cb.message.answer("🎉 Все лоты рассмотрены! Новых лотов нет.")
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
                              text="Ваш лот был отклонен. За подробностями обращайтесь в тех. поддержку.",
                              reply_markup=kb.tech_bot_menu)
    next_lot = await rq.get_next_lot(lot_id)
    if next_lot:
        nx_user = await rq.get_user_data(next_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=f"Лот: <b>#{next_lot.id}</b>\n"
                    f"Стартовая цена: <b>{next_lot.starter_price}</b>🌟\n"
                    f"Следующая минимальная ставка: <b>{next_lot.real_price + 1}</b>🌟\n"
                    f"Цена моментальной покупки: <b>{next_lot.moment_buy_price}</b>🌟\n"
                    f"Продвец: <b>{nx_user.name}</b>\n"
                    f"Время окончания: <b>{next_lot.expired_at.strftime('%Y-%m-%d %H:%M:%S')}</b> (MSK)\n",
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
        await cb.message.edit_text("🎉 Все лоты рассмотрены! Новых лотов нет.")

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^next_lot_\d+$", cb.data))
async def reject_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    next_lot = await rq.get_next_lot(lot_id)
    if next_lot:
        nx_user = await rq.get_user_data(next_lot.seller)
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=f"Лот: <b>#{next_lot.id}</b>\n"
                    f"Стартовая цена: <b>{next_lot.starter_price}</b>🌟\n"
                    f"Следующая минимальная ставка: <b>{next_lot.real_price + 1}</b>🌟\n"
                    f"Цена моментальной покупки: <b>{next_lot.moment_buy_price}</b>🌟\n"
                    f"Продвец: <b>{nx_user.name}</b>\n"
                    f"Время окончания: <b>{next_lot.expired_at.strftime('%d.%m.%Y %H:%M')}</b> (MSK)\n",
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
        await cb.answer("Вы рассмотрели все лоты после данного.")

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r"^prev_lot_\d+$", cb.data))
async def reject_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    prev_lot = await rq.get_previous_lot(lot_id)
    if prev_lot:
        await cb.message.edit_media(media=InputMediaPhoto(
            media=prev_lot.photo_id,
            caption=f"Лот: <b>#{prev_lot.id}</b>\n"
                    f"Стартовая цена: <b>{prev_lot.starter_price}</b>🌟\n"
                    f"Следующая минимальная ставка: <b>{prev_lot.real_price + 1}</b>🌟\n"
                    f"Цена моментальной покупки: <b>{prev_lot.moment_buy_price}</b>🌟\n"
                    f"Продвец: <b>{prev_lot.seller}</b>\n"
                    f"Время окончания: <b>{prev_lot.expired_at.strftime('%d.%m.%Y %H:%M')}</b> (MSK)\n",
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
        await cb.answer("Вы рассмотрели все лоты перед данным.")

@admin_router.callback_query(IsAdminCb(), F.data == "end_moderation")
async def end_moderation(cb: CallbackQuery):
    await cb.message.delete()
    msg = await cb.message.answer("Вы закончили модерировать лоты.")
    await asyncio.sleep(5)
    await msg.delete()

@admin_router.callback_query(IsAdminCb(), F.data == "interrupt_work")
async def interrupt_work(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await state.clear()
    new_message = await cb.message.answer("Вы прервали работу!")
    await asyncio.sleep(5)
    await new_message.delete()
