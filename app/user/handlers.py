import asyncio
import re
import types

from aiogram import F, Router, types

from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.db.models import LotStatus
from app.middlewares import UserDBCheckMiddleware, UserBanCheckMiddleware, UserBanCheckMiddlewareCB

import app.db.requests as rq

from app.filters import IsUser

import app.user.keyboards as kb

from config import PAYMENTS_TOKEN, CHANNEL_ID, status_mapping, BOT_ID, TEXTS

from app.user.handler_functions import bid_lot

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

@user_router.message(IsUser(), CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    lot_uuid = command.args
    if lot_uuid:
        lot = await rq.get_lot_by_uuid(lot_uuid)
        seller = await rq.get_user_data_id(lot.user_id)
        await message.answer_photo(photo=lot.photo_id,
                                   caption=TEXTS["cmd_start_auction_caption"].format(starter_price=lot.starter_price,
                                                                                     real_price=lot.real_price,
                                                                                     min_next_price=lot.real_price + 1,
                                                                                     moment_buy_price=lot.moment_buy_price,
                                                                                     expired_at=lot.expired_at.strftime('%d.%m.%Y %H:%M'),
                                                                                     name=seller.name),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text='Перебить ставку(+1)',
                                                             callback_data=f'bid_1_{lot.id}')],
                                       [InlineKeyboardButton(text='5', callback_data=f'bid_5_{lot.id}'),
                                        InlineKeyboardButton(text="10", callback_data=f'bid_10_{lot.id}'),
                                        InlineKeyboardButton(text="25", callback_data=f'bid_25_{lot.id}')],
                                       [InlineKeyboardButton(text="50", callback_data=f'bid_50_{lot.id}'),
                                        InlineKeyboardButton(text="100", callback_data=f'bid_100_{lot.id}')],
                                       [InlineKeyboardButton(text=f"Купить мгновенно за {lot.moment_buy_price}🌟",
                                                             callback_data=f'buy_now_{lot.id}')]
                                   ])
                                   )
    else:
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

@user_router.message(IsUser(), F.text == "🎫Создать лот")
async def create_lot(message: Message, state: FSMContext):
    await message.answer(text=TEXTS["create_lot_1_msg"],
                         reply_markup=kb.interrupt_work)
    await state.set_state(CreateLot.photo)

@user_router.message(IsUser(), F.photo, CreateLot.photo)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(CreateLot.starter_price)
    await message.answer(TEXTS["create_lot_2_msg"])

@user_router.message(IsUser(), CreateLot.starter_price)
async def set_lots_photo(message: Message, state: FSMContext):
    if message.text and message.text.isdigit() and int(message.text) > 0:
        await state.update_data(starter_price=int(message.text))
        await state.set_state(CreateLot.blitz_price)
        await message.answer(TEXTS["create_lot_3_msg"])
    else:
        await message.answer(TEXTS["create_lot_3.3_msg"])

@user_router.message(IsUser(), CreateLot.blitz_price)
async def set_lots_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.isdigit() and int(message.text) > data['starter_price']:
        await state.update_data(blitz_price=int(message.text))
        await state.set_state(CreateLot.completion_time)
        await message.answer(text=TEXTS["create_lot_3.4_msg"],
                         reply_markup=kb.lot_times_menu)
    else:
        await message.answer(TEXTS["create_lot_3.2_msg"])


@user_router.callback_query(IsUser(), F.data == "one_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours = 1)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                  caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                                  )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()

@user_router.callback_query(IsUser(), F.data == "two_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours = 2)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                  caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                                   )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "four_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=4)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                  caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "eight_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=8)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "ten_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=10)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "twelve_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=12)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "twenty_four_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=24)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "forty_eight_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours=48)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'],
                     pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                          caption=TEXTS["create_lot_end_caption"].format(starter_price=data['starter_price'],
                                                                                 blitz_price=data['blitz_price'],
                                                                                 hours=data['hours'],
                                                                                 name=cb.from_user.first_name
                                                                                 )
                          )
    await cb.message.answer(TEXTS["create_lot_end_notif_msg"])
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "deposit_balance")
async def deposit_balance(cb: CallbackQuery, state: FSMContext):
    await cb.answer("")
    await state.set_state(DepositBalance.number_stars)
    await cb.message.edit_text(text=TEXTS["deposit_balance_msg"],
                               reply_markup=kb.interrupt_work)

@user_router.message(IsUser(), DepositBalance.number_stars)
async def deposit_balance_s(message: Message, state: FSMContext):
    if message.text and message.text.isdigit() and int(message.text) >= 50 and int(message.text) <= 10000:
        await state.update_data(stars=int(message.text))
        data = await state.get_data()
        await message.answer(TEXTS["send_deposit_balance_msg"].format(stars=data['stars']))
        await state.clear()
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title="Пополнение баланса.",
            description=f"Пополнение баланса профиля на {data['stars']}🌟",
            provider_token=PAYMENTS_TOKEN,
            currency="rub",
            photo_url="https://digital-basket-01.wbbasket.ru/vol6/124/a0516b93ae5e8a32ac14e4fc265b575f/1280.jpg",
            photo_width=800,
            photo_height=650,
            photo_size=800,
            payload=f"deposit_balance_{data['stars']}",
            prices=[types.LabeledPrice(label=f"Покупка {data['stars']}🌟", amount=int(data['stars']*1.6*100))],
            need_email=True,
            send_email_to_provider=True
        )
    else:
        await message.answer(TEXTS["limitations_deposit_balance_msg"])

@user_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pcq: PreCheckoutQuery):
    await pcq.bot.answer_pre_checkout_query(pcq.id, ok=True)

@user_router.message(IsUser(), F.successful_payment)
async def process_suc_payment(message: Message):
    stars = int(message.successful_payment.invoice_payload.split("_")[-1])
    await rq.deposit_balance(tg_id=message.from_user.id, stars=stars)
    await message.answer(TEXTS["successful_payment"].format(stars=stars))

@user_router.callback_query(IsUser(), F.data == "interrupt_work")
async def interrupt_work(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await state.clear()
    new_message = await cb.message.answer(TEXTS["interrupt_work_msg"])
    await asyncio.sleep(5)
    await new_message.delete()

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_1_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=1, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_5_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=5, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_10_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=10, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_25_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=25, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_50_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=50, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^bid_100_\d+$", cb.data))
async def outbid_bid_1(cb: CallbackQuery):
    lot_id = int(cb.data.split("_")[-1])
    lot = await rq.get_lot_data(lot_id)
    await bid_lot(lot=lot, bid=100, lot_id=lot_id, cb=cb, user_id=cb.from_user.id)

@user_router.callback_query(IsUser(), lambda cb: re.match(r"^buy_now_\d+$", cb.data))
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

    elif user.balance < lot.real_price:
        await cb.answer()
        await cb.message.answer(text=TEXTS["not_enough_stars"],
                                reply_markup=kb.profile_menu)
        return

    applicant = await rq.get_lot_applicant(lot_id)

    if applicant == cb.from_user.id:
        await cb.answer()
        await cb.message.answer(TEXTS["bet_is_already_yours_msg"])
        return

    await rq.buy_now(lot_id, cb.from_user.id)

    if lot.applicant and lot.applicant == cb.from_user.id:
        await rq.increase_balance(cb.from_user.id, lot.real_price)
    elif lot.applicant and lot.applicant != cb.from_user.id:
        await rq.set_lot_applicant(lot_id, cb.from_user.id)
        await rq.increase_balance(lot.applicant, lot.real_price)
    await rq.decrease_balance(cb.from_user.id, lot.moment_buy_price)
    await cb.bot.send_message(chat_id=cb.from_user.id,
                     text=TEXTS["user_buy_lot_msg"].format(id=lot.id,
                                                           moment_buy_price=lot.moment_buy_price,
                                                           username=seller.username
                                                           ))
    await cb.bot.send_message(chat_id=lot.seller,
                           text=TEXTS["seller_send_gift_msg"].format(id=lot.id,
                                                                     username=cb.from_user.username))
    lot = await rq.get_lot_data(lot_id)
    await cb.bot.edit_message_caption(
        chat_id=f"@{CHANNEL_ID}",
        message_id=lot.message_id,
        caption=TEXTS["sold_lot_caption"].format(starter_price=lot.starter_price,
                                                 moment_buy_price=lot.moment_buy_price,
                                                 seller=seller.name,
                                                 status=status_mapping.get(lot.status.value, "None"),
                                                 name=user.name
                                                 ),
        parse_mode="HTML",
    )
