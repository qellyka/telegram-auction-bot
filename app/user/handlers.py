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

from config import PAYMENTS_TOKEN, CHANNEL_ID, status_mapping, BOT_ID

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
        user = await rq.get_user_data_id(lot.user_id)
        await message.answer_photo(photo=lot.photo_id,
                                   caption=f"Стартовая цена: {lot.starter_price}🌟\n"
                                           f"Последняя ставка: {lot.real_price}🌟\n"
                                           f"Следующая минимальная ставка: {lot.real_price + 1}🌟\n"
                                           f"Блитц цена: {lot.moment_buy_price}🌟\n"
                                           f"Закончится: {lot.expired_at.strftime('%d.%m.%Y %H:%M')} (MSK)\n"
                                           f"Продавец: {user.name}\n",
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
            await message.answer("👋Привет, это бот Аукцион Saharok's/richa\n\n"
                                      "🕒Мы работаем: \n"
                                      "8:00 - 23:00мск, в это время вам ответят в течение 5 - 10 минут!\n\n"
                                      "📌Заказы, пришедшие с 23:00 до 8:00, будут выполнены утром, в порядке очереди.",
                             reply_markup=kb.main_menu)
            await rq.set_new_user(message.from_user.id)
        else:
            await message.answer(text="Выберите, что вы  хотите сделать в меню. 🛠",
                                 reply_markup=kb.main_menu)

@user_router.message(IsUser(), Command("menu"))
async def menu(message: Message):
    await message.answer("Выберите, что вы  хотите сделать в меню. 🛠", reply_markup=kb.main_menu)

@user_router.message(IsUser(), F.text == "🪪Профиль")
async def profile(message: Message):
    user = await rq.get_user_data(message.from_user.id)
    await message.answer(f"👤 Имя пользователя:  {message.from_user.username} \n"
                         f"📍 Количество лотов:  {user.lots} \n"
                         f"💰 Ваш баланс:  {user.balance}🌟 \n",
                         reply_markup=kb.profile_menu)

@user_router.message(IsUser(), F.text == "🛠️Тех. поддержка")
async def create_lot(message: Message):
    await message.answer("❓Если у вас возникли вопросы, то перейдите в нашего бота, чтобы обратиться в службу поддержки ✅",
                         reply_markup=kb.tech_bot_menu)

@user_router.message(IsUser(), F.text == "Вывести 🌟")
async def create_lot(message: Message):
    await message.answer("⚙ Для вывода звёзд, напишите в бот для вывода.",
                         reply_markup=kb.withdraw_bot_menu)

@user_router.message(IsUser(), F.text == "🎫Создать лот")
async def create_lot(message: Message, state: FSMContext):
    await message.answer("📷 Пришлите фото подарка, который вы хотите выставить на продажу(владельца можно замазать). 🎁\n"
                         "🔁Если вы нажали на кнопку случайно, нажмите 'прервать' 🔁",
                         reply_markup=kb.interrupt_work)
    await state.set_state(CreateLot.photo)

@user_router.message(IsUser(), F.photo, CreateLot.photo)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(CreateLot.starter_price)
    await message.answer("🌟 Введите  стартовую цену в звёздах, 🌟️=1,65₽.")

@user_router.message(IsUser(), CreateLot.starter_price)
async def set_lots_photo(message: Message, state: FSMContext):
    if message.text and message.text.isdigit() and int(message.text) > 0:
        await state.update_data(starter_price=int(message.text))
        await state.set_state(CreateLot.blitz_price)
        await message.answer("🌟 Введите  блитц цену в звёздах(цена за которую можно моментально выкупить лот), 🌟️=1,65₽.")
    else:
        await message.answer("🌟 Введите числовое значение, большее нуля.")

@user_router.message(IsUser(), CreateLot.blitz_price)
async def set_lots_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text and message.text.isdigit() and int(message.text) > data['starter_price']:
        await state.update_data(blitz_price=int(message.text))
        await state.set_state(CreateLot.completion_time)
        await message.answer("🕒 Выберете кол-во часов через которое лот будет закрыт, если его не выкупят. 🕒",
                         reply_markup=kb.lot_times_menu)
    else:
        await message.answer("🌟 Введите числовое значение, большее стартовой цены.")


@user_router.callback_query(IsUser(), F.data == "one_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours = 1)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                   caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                           f"Блитц цена: {data['blitz_price']}🌟\n"
                                           f"Длительность лота(в часах): {data['hours']}\n"
                                           f"Продавец: {cb.from_user.username}\n"
                                   )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
    await state.clear()

@user_router.callback_query(IsUser(), F.data == "two_hour", CreateLot.completion_time)
async def set_lot(cb: CallbackQuery, state: FSMContext):
    await state.update_data(hours = 2)
    data = await state.get_data()
    await rq.set_lot(tid=cb.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], pid=data['photo_id'], blitz_price=data['blitz_price'])
    await cb.answer("")
    await cb.message.delete()
    await cb.message.answer_photo(photo=data['photo_id'],
                                   caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                           f"Блитц цена: {data['blitz_price']}🌟\n"
                                           f"Длительность лота(в часах): {data['hours']}\n"
                                           f"Продавец: {cb.from_user.username}\n"
                                   )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
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
                          caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                  f"Блитц цена: {data['blitz_price']}🌟\n"
                                  f"Длительность лота(в часах): {data['hours']}\n"
                                  f"Продавец: {cb.from_user.username}\n"
                          )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
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
                          caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                  f"Блитц цена: {data['blitz_price']}🌟\n"
                                  f"Длительность лота(в часах): {data['hours']}\n"
                                  f"Продавец: {cb.from_user.username}\n"
                          )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
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
                          caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                  f"Блитц цена: {data['blitz_price']}🌟\n"
                                  f"Длительность лота(в часах): {data['hours']}\n"
                                  f"Продавец: {cb.from_user.username}\n"
                          )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
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
                          caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                  f"Блитц цена: {data['blitz_price']}🌟\n"
                                  f"Длительность лота(в часах): {data['hours']}\n"
                                  f"Продавец: {cb.from_user.username}\n"
                          )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
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
                          caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                  f"Блитц цена: {data['blitz_price']}🌟\n"
                                  f"Длительность лота(в часах): {data['hours']}\n"
                                  f"Продавец: {cb.from_user.username}\n"
                          )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
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
                          caption=f"Стартовая цена: {data['starter_price']}🌟\n"
                                  f"Блитц цена: {data['blitz_price']}🌟\n"
                                  f"Длительность лота(в часах): {data['hours']}\n"
                                  f"Продавец: {cb.from_user.username}\n"
                          )
    await cb.message.answer("📝 Ваш лот был отправлен на модерацию, после проверки мы опубликуем его, и вам придёт уведомление! 📝")
    await state.clear()


@user_router.callback_query(IsUser(), F.data == "deposit_balance")
async def deposit_balance(cb: CallbackQuery, state: FSMContext):
    await cb.answer("")
    await state.set_state(DepositBalance.number_stars)
    await cb.message.edit_text("✍ Введите кол-во звезд,на которое вы хотите пополнить свой баланс. 💰\n"
                               "🔁Если вы нажали на кнопку случайно, нажмите 'прервать' 🔁",
                               reply_markup=kb.interrupt_work)

@user_router.message(IsUser(), DepositBalance.number_stars)
async def deposit_balance_s(message: Message, state: FSMContext):
    if message.text and message.text.isdigit() and int(message.text) >= 50 and int(message.text) <= 10000:
        await state.update_data(stars=int(message.text))
        data = await state.get_data()
        await message.answer(f"Сейчас мы пришлём счет, на пополнение баланса на {data['stars']}🌟")
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
            prices=[types.LabeledPrice(label=f"Покупка {data['stars']}🌟", amount=int(data['stars']*1.65*100))],
            need_email=True,
            send_email_to_provider=True
        )
    else:
        await message.answer("📌 Минимальное числовое значение 50, а максимальное 15 000 📌")

@user_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pcq: PreCheckoutQuery):
    await pcq.bot.answer_pre_checkout_query(pcq.id, ok=True)

@user_router.message(IsUser(), F.successful_payment)
async def process_suc_payment(message: Message):
    stars = int(message.successful_payment.invoice_payload.split("_")[-1])
    await rq.deposit_balance(tg_id=message.from_user.id, stars=stars)
    await message.answer(f"🎊 Вам успешно зачислено {stars}🌟️!")

@user_router.callback_query(IsUser(), F.data == "interrupt_work")
async def interrupt_work(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await state.clear()
    new_message = await cb.message.answer("Вы прервали работу!")
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
        await cb.message.answer("Лот уже выкуплен.")
        return

    elif lot.status == LotStatus.EXPIRED:
        await cb.answer()
        await cb.message.delete()
        await cb.message.answer("Лот был закрыт по времени, его никто не купил.")
        return

    elif user.balance < lot.real_price:
        await cb.answer()
        await cb.message.answer("💰На вашем балансе недостаточно звезд⭐, пополните баланс, нажав на кнопку ниже ⬇️",
                                reply_markup=kb.profile_menu)
        return

    applicant = await rq.get_lot_applicant(lot_id)

    if applicant == cb.from_user.id:
        await cb.answer()
        await cb.message.answer("⌛️Вы уже сделали ставку на этот лот, дождитесь пока её перебьют  или купите мгновенно⌛️")
        return

    await rq.buy_now(lot_id, cb.from_user.id)

    if lot.applicant and lot.applicant == cb.from_user.id:
        await rq.increase_balance(cb.from_user.id, lot.real_price)
    elif lot.applicant and lot.applicant != cb.from_user.id:
        await rq.set_lot_applicant(lot_id, cb.from_user.id)
        await rq.increase_balance(lot.applicant, lot.real_price)
    await rq.decrease_balance(cb.from_user.id, lot.moment_buy_price)
    await cb.bot.send_message(chat_id=cb.from_user.id,
                     text=f"Вы выкупили лот #{lot.id} за {lot.moment_buy_price}🌟. В течении часа @{seller.username} должен отправить ваи подарок.")
    await cb.bot.send_message(chat_id=lot.seller,
                           text=f'Ваш лот #{lot.id} закончился. В нем есть победитель @{cb.from_user.username}. В течение часа вы должны отправить подарок, '
                                f'если вы этого не сделаете покупатель может открыть спор и вернуть звезды, а вас забанят!')
    lot = await rq.get_lot_data(lot_id)
    await cb.bot.edit_message_caption(
        chat_id=f"@{CHANNEL_ID}",
        message_id=lot.message_id,
        caption=f"Лот: <b>#{lot.id}</b>\n"
                f"Стартовая цена: <b>{lot.starter_price}</b>🌟\n"
                f"Последняя ставка: <b>{lot.moment_buy_price}</b>🌟\n"
                f"Продвец: <b>{seller.name}</b>\n"
                f"Статус: <b>{status_mapping.get(lot.status.value, "None")}</b>\n"
                f"Покупатель: <b>{cb.from_user.first_name}</b>",
        parse_mode="HTML",
    )
