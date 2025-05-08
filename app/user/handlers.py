import asyncio
import logging
import random
import re
import string
import types

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest

from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.util import await_only

from app.db.models import LotStatus
from app.middlewares import UserDBCheckMiddleware, UserBanCheckMiddleware, UserBanCheckMiddlewareCB

import app.db.requests as rq

from app.filters import IsUser, IsUserCb

import app.user.keyboards as kb

from config import PAYMENTS_TOKEN, CHANNEL_ID, status_mapping, BOT_ID, TEXTS, STAR_K

from app.user.handler_functions import bid_lot, create_payment_link

user_router = Router()

user_router.message.outer_middleware(UserDBCheckMiddleware())
user_router.message.outer_middleware(UserBanCheckMiddleware())
user_router.message.outer_middleware(UserBanCheckMiddlewareCB())

class DepositBalance(StatesGroup):
    number_stars = State()

class CreateLot(StatesGroup):
    photo = State()
    starter_price = State()
    blitz_price = State()
    completion_time = State()

class WithdrawStars(StatesGroup):
    value = State()
    bank = State()
    number = State()

class UserPop():
    name: str

payment_msg = {}

@user_router.message(IsUser(), CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    arg = command.args
    print(arg)
    if arg:
        if len(arg) == 10:
            inviter = await rq.get_user_data_ref(arg)
            user = await rq.get_user_data(message.from_user.id)
            if user.id != inviter.id and user.is_new:
                await rq.set_user_referral(referral_id=inviter.telegram_id , tid=message.from_user.id)
                await message.answer(TEXTS['link_reg'].format(inviter=inviter.username))
            return

        else:
            lot = await rq.get_lot_by_uuid(arg)
            seller = await rq.get_user_data_id(lot.user_id)
            await message.answer_photo(photo=lot.photo_id,
                caption=TEXTS["cmd_start_auction_caption"].format(
                    starter_price=lot.starter_price,
                    real_price=lot.real_price,
                    min_next_price=lot.real_price + 1,
                    moment_buy_price=lot.moment_buy_price,
                    expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                    name=seller.name),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Перебить ставку(+1)', callback_data=f'bid_1_{lot.id}')],
                    [InlineKeyboardButton(text='5', callback_data=f'bid_5_{lot.id}'),
                     InlineKeyboardButton(text="10", callback_data=f'bid_10_{lot.id}'),
                     InlineKeyboardButton(text="25", callback_data=f'bid_25_{lot.id}')],
                    [InlineKeyboardButton(text="50", callback_data=f'bid_50_{lot.id}'),
                     InlineKeyboardButton(text="100", callback_data=f'bid_100_{lot.id}')],
                    [InlineKeyboardButton(text=f"Купить мгновенно за {lot.moment_buy_price}🌟", callback_data=f'buy_now_{lot.id}')]
                ])
            )
            return

    user = await rq.get_user_data(message.from_user.id)
    if user.is_new:
        await message.answer(text=TEXTS["cmd_start_msg"].format(name=user.name),
                             reply_markup=kb.main_menu)
        await rq.set_new_user(message.from_user.id)
    else:
        await message.answer(text=TEXTS["main_menu_msg"],
                             reply_markup=kb.main_menu)


@user_router.message(IsUser(), Command("menu"))
async def menu(message: Message):
    await message.answer(text=TEXTS["main_menu_msg"],
                         reply_markup=kb.main_menu)

@user_router.message(IsUser(), F.text == "🪪Профиль")
async def profile(message: Message):
    user = await rq.get_user_data(message.from_user.id)
    await message.answer(text=TEXTS["user_profile_msg"].format(username=user.username,
                                                               lots=user.lots,
                                                               balance=user.balance),
                         reply_markup=kb.profile_menu)

@user_router.message(IsUser(), F.text == "🛠️Тех. поддержка")
async def create_lot(message: Message):
    await message.answer(text=TEXTS["support_msg"],
                         reply_markup=kb.tech_bot_menu)

@user_router.message(IsUser(), F.text == "Вывести 🌟")
async def create_lot(message: Message):
    await message.answer(text=TEXTS["withdraw_stars_msg"],
                         reply_markup=kb.withdraw_bot_menu)

@user_router.callback_query(IsUserCb(), F.data == "withdraw_stars")
async def withdraw_stars_value(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.edit_text(TEXTS['write_value_of_stars_msg'])
    await state.set_state(WithdrawStars.value)

@user_router.message(IsUser(), WithdrawStars.value)
async def withdraw_stars_bank(message: Message, state: FSMContext):
    user = await rq.get_user_data(message.from_user.id)
    if user.balance < 50:
        await message.answer(TEXTS["withdraw_from_50_stars"],
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Отменить",
                                                           callback_data="interrupt_work")]
                                 ]))
    elif message.text and message.text.isdigit() and int(message.text) <= user.balance and int(message.text) >= 50:
        await state.update_data(value=int(message.text))
        await message.answer(TEXTS['choose_bank_msg'],
                             reply_markup=kb.banks_menu)
        await state.set_state(WithdrawStars.bank)
    else:
        await message.answer(TEXTS['write_correct_value_of_stars'])

@user_router.callback_query(IsUserCb(), F.data == "tinkoff", WithdrawStars.bank)
async def withdraw_stars_number(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await state.update_data(bank="tinkoff")
    await cb.message.edit_text(TEXTS['write_your_account_number'])
    await state.set_state(WithdrawStars.number)

@user_router.callback_query(IsUserCb(), F.data == "sberbank", WithdrawStars.bank)
async def withdraw_stars_number(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await state.update_data(bank="sberbank")
    await cb.message.answer(TEXTS['write_your_account_number'])
    await state.set_state(WithdrawStars.number)

@user_router.callback_query(IsUserCb(), F.data == "alfabank", WithdrawStars.bank)
async def withdraw_stars_number(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await state.update_data(bank="alfabank")
    await cb.message.answer(TEXTS['write_your_account_number'])
    await state.set_state(WithdrawStars.number)

@user_router.callback_query(IsUserCb(), F.data == "stars", WithdrawStars.bank)
async def withdraw_stars_number(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await state.update_data(bank="stars")
    await state.update_data(number=cb.from_user.username)
    await cb.message.answer('Подтвердите отправку заявки.',
                         reply_markup=kb.withdraw_menu)

@user_router.message(IsUser(), WithdrawStars.number)
async def withdraw_stars_end(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer('Подтвердите отправку заявки.',
                         reply_markup=kb.withdraw_menu)

@user_router.callback_query(IsUserCb(), F.data == "send_withdraw_blank")
async def send_withdraw_blank(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    data = await state.get_data()
    await rq.decrease_balance(cb.from_user.id, data['value'])
    await rq.add_new_blank(cb.from_user.id, stars=data['value'], bank=data['bank'], number=data['number'])
    await cb.message.edit_text(TEXTS['blank_send_to_administrators'])
    await rq.notify_withdrawers(message=TEXTS['new_withdrawal_notification'], bot=cb.bot)
    await state.clear()

@user_router.callback_query(IsUserCb(), F.data == "cancel_withdraw_blank")
async def send_withdraw_blank(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    msg = await cb.message.answer('Заявка была отменена.')
    await asyncio.sleep(5)
    await msg.delete()
    await state.clear()


@user_router.message(IsUser(), F.text == "🎫Создать лот")
async def create_lot(message: Message, state: FSMContext):
    await message.answer(text=TEXTS["create_lot_1_msg"],
                         reply_markup=kb.interrupt_work)
    await state.set_state(CreateLot.photo)

@user_router.message(IsUser(), F.text == "👨‍👩‍👧‍👦Реферальная программа")
async def create_ref_link_msg(message: Message):
    await message.answer(text=TEXTS['ref_msg_prev'],
                         parse_mode="HTML",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text=TEXTS['create_ref_link'],
                                                   callback_data="create_ref_link")]
                         ]))

@user_router.callback_query(IsUserCb(), F.data == "create_ref_link")
async def create_ref_link(cb: CallbackQuery):
    await cb.answer()
    user = await rq.get_user_data(cb.from_user.id)

    existing_referral = await rq.get_user_referral(user.id)
    if existing_referral:
        await cb.message.answer(text=TEXTS['u_have_ref_link'])
        return

    if user.ref_id:
        await cb.message.answer(text=TEXTS['u_are_referral'])
        return

    link =  ''.join(random.choices(string.ascii_uppercase, k=10))

    await cb.message.answer(text=TEXTS['your_ref_link'],
                            parse_mode='HTML',)
    await rq.add_new_referral_link(link, cb.from_user.id)
    await cb.message.answer(text=TEXTS['earn_with_lotoro'],
                            parse_mode='HTML',
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text=TEXTS['join_to_lotoro'],
                                                      url=f"https://t.me/{BOT_ID}?start={link}")]
                            ]))

@user_router.message(IsUser(), F.photo, CreateLot.photo)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(CreateLot.starter_price)
    await message.answer(TEXTS["create_lot_2_msg"])

@user_router.message(IsUser(), CreateLot.starter_price)
async def set_lots_photo(message: Message, state: FSMContext):
    if message.text and message.text.isdigit() and int(message.text) > 0 and int(message.text) < 2000000:
        await state.update_data(starter_price=int(message.text))
        await state.set_state(CreateLot.blitz_price)
        await message.answer(TEXTS["create_lot_3_msg"])
    else:
        await message.answer(TEXTS["create_lot_3.1_msg"])

@user_router.message(IsUser(), CreateLot.blitz_price)
async def set_lots_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.isdigit() and int(message.text) > data['starter_price'] and int(message.text) < 2000000:
        await state.update_data(blitz_price=int(message.text))
        await state.set_state(CreateLot.completion_time)
        await message.answer(text=TEXTS["create_lot_4_msg"],
                         reply_markup=kb.lot_times_menu)
    else:
        await message.answer(TEXTS["create_lot_3.2_msg"])


@user_router.callback_query(IsUserCb(), F.data == "one_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours = 1)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                  caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                                  )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()

@user_router.callback_query(IsUserCb(), F.data == "two_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours = 2)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                  caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                                   )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "four_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=4)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                  caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "eight_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=8)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "ten_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=10)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "twelve_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=12)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "twenty_four_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=24)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "forty_eight_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=48)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await rq.notify_admins(TEXTS['new_lot_notification'], cb.bot)
    await state.clear()


@user_router.callback_query(IsUserCb(), F.data == "deposit_balance")
async def deposit_balance(cb: CallbackQuery, state: FSMContext):
    try:
        await cb.answer()
    except Exception as e:
        logging.warning(f"Не удалось ответить на callback: {e}")
    await state.set_state(DepositBalance.number_stars)
    msg = await cb.message.edit_text(text=TEXTS["deposit_balance_msg"].format(star_k=STAR_K),
                               reply_markup=kb.interrupt_work)
    await state.update_data(msg_id=msg.message_id)

@user_router.message(IsUser(), DepositBalance.number_stars)
async def deposit_balance_s(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.isdigit() and int(message.text) >= 50 and int(message.text) <= 10000:
        await message.bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=data['msg_id'],
                                            text=TEXTS['deposit_balance_msg_2'])
        await state.update_data(stars=int(message.text))
        data = await state.get_data()
        user = await rq.get_user_data(message.from_user.id)
        url = await create_payment_link(dep=data['stars']*STAR_K, payment_label=user.telegram_id)
        msg = await message.answer(TEXTS["send_deposit_balance_msg"].format(stars=data['stars'],
                                                                            rub=data['stars']*STAR_K),
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                    [InlineKeyboardButton(text="Оплатить",
                                                          url=url)],
                                    [InlineKeyboardButton(text="Отменить",
                                                          callback_data="interrupt_work")]
                                 ]))
        await state.clear()
        payment_msg[user.telegram_id] = msg.message_id
    else:
        await message.answer(TEXTS["limitations_deposit_balance_msg"])


# @user_router.message(IsUserCb(), DepositBalance.number_stars)
# async def deposit_balance_s(message: Message, state: FSMContext):
#     if message.text and message.text.isdigit() and int(message.text) >= 50 and int(message.text) <= 10000:
#         await state.update_data(stars=int(message.text))
#         data = await state.get_data()
#         await message.answer(TEXTS["send_deposit_balance_msg"].format(stars=data['stars']))
#         await state.clear()
#         await message.bot.send_invoice(
#             chat_id=message.chat.id,
#             title="Пополнение баланса.",
#             description=f"Пополнение баланса профиля на {data['stars']}🌟",
#             provider_token=PAYMENTS_TOKEN,
#             currency="rub",
#             photo_url="https://digital-basket-01.wbbasket.ru/vol6/124/a0516b93ae5e8a32ac14e4fc265b575f/1280.jpg",
#             photo_width=800,
#             photo_height=650,
#             photo_size=800,
#             payload=f"deposit_balance_{data['stars']}",
#             prices=[types.LabeledPrice(label=f"Покупка {data['stars']}🌟", amount=int(data['stars']*STAR_K*100))],
#             need_email=True,
#             send_email_to_provider=True
#         )
#     else:
#         await message.answer(TEXTS["limitations_deposit_balance_msg"])
#
# @user_router.pre_checkout_query(lambda query: True)
# async def pre_checkout_query(pcq: PreCheckoutQuery):
#     await pcq.bot.answer_pre_checkout_query(pcq.id, ok=True)
#
# @user_router.message(IsUser(), F.successful_payment)
# async def process_suc_payment(message: Message):
#     user = await rq.get_user_data(message.from_user.id)
#     stars = int(message.successful_payment.invoice_payload.split("_")[-1])
#     await rq.deposit_balance(tg_id=message.from_user.id, stars=stars)
#     if user.ref_id:
#         await rq.deposit_balance(tg_id=user.ref_id, stars=int(stars*5/100))
#         await message.bot.send_message(chat_id=user.ref_id,
#                                        text=TEXTS['ref_stars'].format(stars=stars*5/100))
#     await message.answer(TEXTS["successful_payment"].format(stars=stars))

@user_router.callback_query(IsUserCb(), F.data == "interrupt_work")
async def interrupt_work(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await state.clear()
    new_message = await cb.message.answer(TEXTS["interrupt_work_msg"])
    await asyncio.sleep(5)
    await new_message.delete()

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^bid_1_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=1, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^bid_5_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=5, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^bid_10_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=10, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^bid_25_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=25, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^bid_50_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=50, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^bid_100_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=100, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^buy_now_\d+$", cb.data))
async def buy_now(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    seller = await rq.get_user_data(lot.seller)
    user = await rq.get_user_data(cb.from_user.id)

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

    elif lot.moment_buy_price < lot.real_price:
        await cb.answer()
        await cb.message.answer(TEXTS["moment_price_men_real_price"])
        return

    elif user.balance < lot.real_price:
        await cb.answer()
        await cb.message.answer(text=TEXTS["not_enough_stars"],
                                reply_markup=kb.profile_menu)
        return

    await rq.buy_now(lot_id, cb.from_user.id, lot.moment_buy_price)

    if lot.applicant and lot.applicant == cb.from_user.id:
        await rq.increase_balance(cb.from_user.id, lot.real_price)
    elif lot.applicant and lot.applicant != cb.from_user.id:
        await rq.set_lot_applicant(lot_id, cb.from_user.id)
        await rq.increase_balance(lot.applicant, lot.real_price)

    await rq.decrease_balance(cb.from_user.id, lot.moment_buy_price)

    sell_msg = await cb.bot.send_message(chat_id=lot.seller,
                              text=TEXTS["seller_send_gift_msg"].format(id=lot.id,
                                                                        username=cb.from_user.username),
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                  [InlineKeyboardButton(text="Открыть спор",
                                                        url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
                              ]))

    await cb.bot.send_message(chat_id=cb.from_user.id,
                              text=TEXTS["user_buy_lot_msg"].format(id=lot.id,
                                                                    moment_buy_price=lot.moment_buy_price,
                                                                    username=seller.username
                                                                    ),
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                [InlineKeyboardButton(text="Подтвердить отправку",
                                                                      callback_data=f"accept_trade_{lot.id}_{sell_msg.message_id}")],
                                                [InlineKeyboardButton(text="Открыть спор",
                                                                      url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
                               ]))
    lot = await rq.get_lot_data(lot_id)
    await cb.bot.edit_message_caption(
        chat_id=f"@{CHANNEL_ID}",
        message_id=lot.message_id,
        caption=TEXTS["sold_lot_caption"].format(starter_price=lot.starter_price,
                                                 moment_buy_price=lot.moment_buy_price,
                                                 seller=seller.name,
                                                 status=status_mapping.get(lot.status.value, "None"),
                                                 name=user.name,
                                                 id=lot.id
                                                 ),
        parse_mode="HTML",
    )
    await cb.answer()

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^accept_trade_\d+_\d+$", cb.data))
async def accept_trade(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-2])
    lot = await rq.get_lot_data(lot_id)
    seller = await rq.get_user_data(lot.seller)
    await cb.message.delete()
    await cb.message.answer("Благодарим вас за покупку, ждём вас сново!")
    await rq.increase_balance(seller.telegram_id, lot.real_price)
    await cb.bot.edit_message_text(chat_id=seller.telegram_id,
                                         message_id=int(cb.data.split("_")[-1]),
                                         text=f"Вам переведены звезды в кол-ве {lot.real_price}🌟, за успешную продажу подарка #{lot.id}. Бладгодарим вас и ждем сново!")

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^deny_trade_\d+_\d+$", cb.data))
async def deny_trade(cb: CallbackQuery):
    await cb.answer()
    lot_id = int(cb.data.split("_")[-2])
    lot = await rq.get_lot_data(lot_id)
    seller = await rq.get_user_data(lot.seller)
    if cb.message:
        try:
            await cb.message.delete()
            await cb.bot.delete_message(chat_id=seller.telegram_id,
                                        message_id=int(cb.data.split("_")[-1]))
        except TelegramBadRequest as e:
            if "message to delete not found" not in str(e) and "message is not modified" not in str(e):
                raise
    user_msg = await cb.bot.send_message(chat_id=lot.applicant,
                                         text="Вы открыли спор, т.к. вам не отправили подарок. Сообщение было отправлено админу, просим вас также написать в тех. поддержку, чтобы ускорить процесс.",
                                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                             [InlineKeyboardButton(text="Написать в тех. поддержку ⚙",
                                                                   url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
                                         ]))
    sell_msg = await cb.bot.send_message(chat_id=seller.telegram_id,
                                   text=f"@{cb.from_user.username} открыл спор, т.к вы не отправили подарок, если вы отправили подарок, а пользователь не подтвердил отправку, обратитесь в тех. поддержку.",
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text="Написать в тех. поддержку ⚙",
                                                             url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
                                   ])
                                   )

    await rq.notify_admins(TEXTS['new_dispute_notification'], cb.bot)
    await rq.add_new_dispute(lot_id, user_msg.message_id, sell_msg.message_id)


@user_router.message(IsUser(), F.text == "📊 Мои аукционы")
async def profile(message: Message):
    await message.answer("Выберите какие именно лоты вы хотите посмотреть.",
                         reply_markup=kb.auction_menu)

@user_router.message(IsUser(), F.text == "🔹 Мои лоты")
async def my_lots(message: Message):
    lot = await rq.get_first_user_lot(message.from_user.id)
    if lot:
        if lot.applicant:
            user = await rq.get_user_data(lot.applicant)
        else:
            user = UserPop()
            user.name = "Нет"
        await message.answer_photo(photo=lot.photo_id,
                                   caption=TEXTS['user_lot_caption'].format(id=lot.id,
                                                                            starter_price=lot.starter_price,
                                                                            real_price=lot.real_price,
                                                                            min_next_price=lot.real_price+1,
                                                                            moment_buy_price=lot.moment_buy_price,
                                                                            name=user.name,
                                                                            expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                                            status=status_mapping.get(lot.status.value)),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                      callback_data=f"prev_lot_{lot.id}"),
                InlineKeyboardButton(text="⏭️ Следующий лот",
                                      callback_data=f"next_lot_{lot.id}")],
                [InlineKeyboardButton(text="🔚 Завершить просмотр",
                                      callback_data="end_moderation")]]),
                                   parse_mode='HTML')
    else:
        await message.answer("Вы не создали пока ни одного лота.")

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^next_lot_\d+$", cb.data))
async def next_user_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    next_lot = await rq.get_next_user_lot(lot_id, cb.from_user.id)
    if next_lot:
        try:
            await cb.answer()
        except Exception as e:
            logging.warning(f"Не удалось ответить на callback: {e}")
        if next_lot.applicant:
            user = await rq.get_user_data(next_lot.applicant)
        else:
            user = UserPop()
            user.name = "Нет"
        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=TEXTS['user_lot_caption'].format(id=next_lot.id,
                                                     starter_price=next_lot.starter_price,
                                                     real_price=next_lot.real_price,
                                                     min_next_price=next_lot.real_price + 1,
                                                     moment_buy_price=next_lot.moment_buy_price,
                                                     name=user.name,
                                                     expired_at=next_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                     status=status_mapping.get(next_lot.status.value)),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_{next_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_{next_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить просмотр",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.answer(TEXTS["reviewed_all_lots_after_this_msg"])


@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^prev_lot_\d+$", cb.data))
async def previous_user_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    prev_lot = await rq.get_previous_user_lot(lot_id, cb.from_user.id)
    if prev_lot:
        try:
            await cb.answer()
        except Exception as e:
            logging.warning(f"Не удалось ответить на callback: {e}")
        if prev_lot.applicant:
            user = await rq.get_user_data(prev_lot.applicant)
        else:
            user = UserPop()
            user.name = "Нет"

        await cb.message.edit_media(media=InputMediaPhoto(
            media=prev_lot.photo_id,
            caption=TEXTS['user_lot_caption'].format(id=prev_lot.id,
                                                     starter_price=prev_lot.starter_price,
                                                     real_price=prev_lot.real_price,
                                                     min_next_price=prev_lot.real_price + 1,
                                                     moment_buy_price=prev_lot.moment_buy_price,
                                                     name=user.name,
                                                     expired_at=prev_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                     status=status_mapping.get(prev_lot.status.value)),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_{prev_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_{prev_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить просмотр",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.answer(TEXTS["reviewed_all_lots_before_this_msg"])


@user_router.message(IsUser(), F.text == "🔹 Мои ставки")
async def my_bids(message: Message):
    lot = await rq.get_first_user_lot_bid(message.from_user.id)
    if lot:
        seller = await rq.get_user_data(lot.seller)
        await message.answer_photo(photo=lot.photo_id,
                                   caption=TEXTS['user_lot_caption_bid'].format(id=lot.id,
                                                                            starter_price=lot.starter_price,
                                                                            real_price=lot.real_price,
                                                                            min_next_price=lot.real_price+1,
                                                                            moment_buy_price=lot.moment_buy_price,
                                                                            name=seller.name,
                                                                            expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                                            status=status_mapping.get(lot.status.value)),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                      callback_data=f"prev_lot_bid_{lot.id}"),
                InlineKeyboardButton(text="⏭️ Следующий лот",
                                      callback_data=f"next_lot_bid_{lot.id}")],
                [InlineKeyboardButton(text="🔚 Завершить просмотр",
                                      callback_data="end_moderation")]]),
                                   parse_mode='HTML')
    else:
        await message.answer("Вы не сделали ни одной ставки или вашу ставку перебили.")

@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^next_lot_bid_\d+$", cb.data))
async def next_user_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    next_lot = await rq.get_next_user_lot_bid(lot_id, cb.from_user.id)
    if next_lot:
        try:
            await cb.answer()
        except Exception as e:
            logging.warning(f"Не удалось ответить на callback: {e}")
        seller = await rq.get_user_data(next_lot.seller)

        await cb.message.edit_media(media=InputMediaPhoto(
            media=next_lot.photo_id,
            caption=TEXTS['user_lot_caption_bid'].format(id=next_lot.id,
                                                     starter_price=next_lot.starter_price,
                                                     real_price=next_lot.real_price,
                                                     min_next_price=next_lot.real_price + 1,
                                                     moment_buy_price=next_lot.moment_buy_price,
                                                     name=seller.name,
                                                     expired_at=next_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                     status=status_mapping.get(next_lot.status.value)),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_bid_{next_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_bid_{next_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить просмотр",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.answer(TEXTS["reviewed_all_lots_after_this_msg"])


@user_router.callback_query(IsUserCb(), lambda cb: re.match(r"^prev_lot_bid_\d+$", cb.data))
async def previous_user_lot(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    prev_lot = await rq.get_previous_user_lot_bid(lot_id, cb.from_user.id)
    if prev_lot:
        try:
            await cb.answer()
        except Exception as e:
            logging.warning(f"Не удалось ответить на callback: {e}")
        seller = await rq.get_user_data(prev_lot.seller)

        await cb.message.edit_media(media=InputMediaPhoto(
            media=prev_lot.photo_id,
            caption=TEXTS['user_lot_caption_bid'].format(id=prev_lot.id,
                                                     starter_price=prev_lot.starter_price,
                                                     real_price=prev_lot.real_price,
                                                     min_next_price=prev_lot.real_price + 1,
                                                     moment_buy_price=prev_lot.moment_buy_price,
                                                     name=seller.name,
                                                     expired_at=prev_lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                     status=status_mapping.get(prev_lot.status.value)),
            parse_mode="HTML")
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏮️ Предыдущий лот",
                                  callback_data=f"prev_lot_bid_{prev_lot.id}"),
            InlineKeyboardButton(text="⏭️ Следующий лот",
                                  callback_data=f"next_lot_bid_{prev_lot.id}")],
            [InlineKeyboardButton(text="🔚 Завершить просмотр",
                                  callback_data="end_moderation")]])
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await cb.answer(TEXTS["reviewed_all_lots_before_this_msg"])

@user_router.callback_query(IsUserCb(), F.data == "end_moderation")
async def end_moderation(cb: CallbackQuery):
    await cb.message.delete()
    msg = await cb.message.answer(TEXTS["end_watching_msg"])
    await asyncio.sleep(5)
    await msg.delete()

