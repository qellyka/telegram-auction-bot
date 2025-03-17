from aiogram import F, Router, types

import re

from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.middlewares import UserDBCheckMiddleware

import app.db.requests as rq

from app.filters import IsAdmin, IsAdminCb

import app.admin.keyboards as kb

from config import CHANNEL_ID

admin_router = Router()

admin_router.message.outer_middleware(UserDBCheckMiddleware())

@admin_router.message(IsAdmin(), CommandStart())
async def menu(message: Message):
    await message.answer('Выберете, что хотите сделать в меню', reply_markup=kb.admin_menu)






@admin_router.message(IsAdmin(), F.text == '🎫Посмотреть новые лоты')
async def view_new_lots(message: Message):
    lots = await rq.get_new_lots()
    if lots:
        for lot in lots:
            await message.answer_photo(photo=lot['photo_id'],
                                       caption=f'Стартовая цена: {lot["starter_price"]}⭐\n'
                                               f'Цена моментальной покупки: {lot["moment_buy_price"]}⭐\n'
                                               f'Продавец: {lot["seller"]}\n'f''
                                               f'Время окончания: {lot["completion_time"]}\n',
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                            [InlineKeyboardButton(text='Одобрить лот',
                                                            callback_data=f'approve_lot_{lot["id"]}')],
                                                            [InlineKeyboardButton(text='Оклонить лот\n',
                                                            callback_data=f'reject_lot_{lot["id"]}')],
                                                    ])
                                       )
    else:
        await message.answer('Новых лотов нет.')


@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r'^approve_lot_\d+$', cb.data))
async def approve_lot(cb: CallbackQuery):
    print('Я ЕБАЛ БАБАЙКУ')
    print('\n\n\n')
    lot_id = int(cb.data.split('_')[-1])
    await rq.approve_lot(lot_id=lot_id)
    lot = await rq.get_lot_data(lot_id=lot_id)
    await cb.bot.send_photo(chat_id='@auction_saharok',
                            photo=lot.photo_id,
                            caption=f'Стартовая цена: {lot.starter_price}⭐\n'
                                    f'Цена перебивки: {lot.real_price + lot.real_price / 100 * 5}⭐\n'
                                    f'Цена моментальной покупки: {lot.moment_buy_price}⭐\n'
                                    f'Продавец: {lot.seller}\n'f''
                                    f'Время окончания: {lot.completion_time}\n',
                              )
    await cb.answer('Лот №' + str(lot_id) + ' одобрен.')

@admin_router.callback_query(IsAdminCb(), lambda cb: re.match(r'^reject_lot_\d+$', cb.data))
async def reject_lot(cb: CallbackQuery):
    print('Я ЕБАЛ БАБАЙКУ')
    lot_id = int(cb.data.split('_')[-1])
    await rq.reject_lot(lot_id=lot_id, tg_id=cb.from_user.id)
    await cb.answer('Лот №' + str(lot_id) + ' отклонен.')