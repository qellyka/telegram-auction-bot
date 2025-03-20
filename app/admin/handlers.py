from aiogram import F, Router, types

import re

from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.util import await_only

from app.middlewares import UserDBCheckMiddleware

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.db.requests as rq

from app.filters import IsAdmin, IsAdminCb

import app.admin.keyboards as kb

admin_router = Router()

admin_router.message.outer_middleware(UserDBCheckMiddleware())

class ManageUser(StatesGroup):
    username = State()

@admin_router.message(IsAdmin(), Command('menu'))
async def menu(message: Message):
    await message.answer('Выберите, что вы  хотите сделать в меню. 🛠', reply_markup=kb.admin_menu)

@admin_router.message(IsAdmin(), F.text == '🛠️Вопросы пользователей')
async def tech_channel(message: Message):
    await message.answer(text='⁉️Перейдите в чат тех поддержки, для того, чтобы посмотреть вопросы других пользователей⁉️',
                         reply_markup=kb.tech_channel_menu)

@admin_router.message(IsAdmin(), F.text == '🎫Посмотреть новые лоты')
async def view_new_lots(message: Message):
    lots = await rq.get_new_lots()
    if lots:
        for lot in lots:
            await message.answer_photo(photo=lot['photo_id'],
                                       caption=f'Стартовая цена: {lot["starter_price"]}⭐\n'
                                               f'Цена моментальной покупки: {lot["moment_buy_price"]}⭐\n'
                                               f'Продавец: {lot["seller"]}\n'f''
                                               f'Длительность лота: {lot['expired_time']}\n',
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                            [InlineKeyboardButton(text='Одобрить лот',
                                                                                  callback_data=f'approve_lot_{lot["id"]}')],
                                                            [InlineKeyboardButton(text='Оклонить лот\n',
                                                                                  callback_data=f'reject_lot_{lot["id"]}')],
                                                    ])
                                       )
    else:
        await message.answer('🙅 Новых лотов сейчас нет. ')


@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r'^approve_lot_\d+$', cb.data))
async def approve_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split('_')[-1])
    await rq.approve_lot(lot_id=lot_id)
    lot = await rq.get_lot_data(lot_id=lot_id)
    user = await rq.get_user_data_id(lot.user_id)
    message = await cb.bot.send_photo(chat_id='@auction_saharok',
                            photo=lot.photo_id,
                            caption=f'Стартовая цена: {lot.starter_price}⭐\n'
                                    f'Цена перебивки: {lot.real_price + lot.real_price / 100 * 5}⭐\n'
                                    f'Цена моментальной покупки: {lot.moment_buy_price}⭐\n'
                                    f'Продавец: {lot.seller}\n'f''
                                    f'Время окончания: {lot.expired_at.strftime("%Y-%m-%d %H:%M:%S")}\n',
                              )
    await cb.answer('Лот №' + str(lot_id) + ' одобрен.')
    await cb.message.delete()
    await cb.bot.send_message(chat_id=user.telegram_id,
                                        text='✅ Ваш лот был одобрен и выставлен на продажу.\n'
                                             f'🔗Ссылка на ваш лот 🔗 : https://t.me/auction_saharok/{message.message_id}')

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r'^reject_lot_\d+$', cb.data))
async def reject_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split('_')[-1])
    lot = await rq.get_lot_data(lot_id=lot_id)
    user = await rq.get_user_data_id(lot.user_id)
    await rq.reject_lot(lot_id=lot_id, tg_id=cb.from_user.id)
    await cb.answer('Лот №' + str(lot_id) + ' отклонен.')
    await cb.message.delete()
    await cb.bot.send_message(chat_id=user.telegram_id,
                              text='Ваш лот был отклонен. За подробностями обращайтесь в тех. поддержку.',
                              reply_markup=kb.tech_bot_menu)

@admin_router.message(IsAdmin(), F.text == '🪪Управление пользователями')
async def manage_users(message: Message, state: FSMContext):
    await state.set_state(ManageUser.username)
    await message.answer('🧑‍💻 Введите username пользователя (без @).')

@admin_router.message(IsAdmin(), ManageUser.username)
async def manage_users_state(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    user = await rq.get_user_by_username(data['username'])
    if user and not(user.is_admin):
        if user.is_banned:
            await message.answer(text=f'👤 Имя пользователя:  {user.username} \n'
                                      f'📍 Количество лотов:  {user.lots} \n'
                                      f'💰 Баланс пользователя:  {user.balance}⭐ \n',
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                [InlineKeyboardButton(text='Разбанить пользователя',
                                                                      callback_data=f'unban_user_{user.telegram_id}')],
                                                [InlineKeyboardButton(text='Посмотреть лоты пользователя',
                                                                      callback_data=f'user_lots_{user.telegram_id}')],
                                                [InlineKeyboardButton(text='Написать пользователю',
                                                                      url=f"tg://user?id={user.telegram_id}")],
                                 ])
                                 )
            await state.clear()
        else:
            await message.answer(text=f'👤 Имя пользователя:  {user.username} \n'
                                      f'📍 Количество лотов:  {user.lots} \n'
                                      f'💰 Баланс пользователя:  {user.balance}⭐ \n',
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text='Забанить пользователя',
                                                           callback_data=f'ban_user_{user.telegram_id}')],
                                     [InlineKeyboardButton(text='Посмотреть лоты пользователя',
                                                           callback_data=f'user_lots_{user.telegram_id}')],
                                     [InlineKeyboardButton(text='Написать пользователю',
                                                           url=f"tg://user?id={user.telegram_id}")],
                                 ])
                                 )
            await state.clear()
    elif user and user.is_admin:
        await message.answer('❌ Вы не можете просматривать профили администраторов ❌')
    else:
        await message.answer('❌ Пользователь  не был найден ❌')


@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r'^ban_user_\d+$', cb.data))
async def ban_user(cb: CallbackQuery):
    tg_id = int(cb.data.split('_')[-1])
    await rq.ban_user(tid=tg_id)
    await cb.message.edit_text('Пользователь успешно забанен.')
    await cb.bot.send_message(chat_id=tg_id,
                              text='🚫 Вы были забанены 🚫 \nЕсли это произошло по ошибке, то обратитесь в тех поддержку.❗️',
                              reply_markup=kb.tech_bot_menu)

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r'^unban_user_\d+$', cb.data))
async def ban_user(cb: CallbackQuery):
    tg_id = int(cb.data.split('_')[-1])
    await rq.unban_user(tid=tg_id)
    await cb.message.edit_text('Пользователь успешно разбанен.')
    await cb.bot.send_message(chat_id=tg_id,
                              text='❗️Вы были разабнены❗️\n⚠️ Повторные нарушения могут привести к бану навсегда! Советуем соблюдать правила. ')






