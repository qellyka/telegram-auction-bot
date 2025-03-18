import types

from aiogram import F, Router, types

from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.middlewares import UserDBCheckMiddleware

import app.db.requests as rq

from app.filters import IsUser

import app.user.keyboards as kb

from config import PAYMENTS_TOKEN

user_router = Router()

user_router.message.outer_middleware(UserDBCheckMiddleware())

class DepositBalance(StatesGroup):
    number_stars = State()

class CreateLot(StatesGroup):
    photo = State()
    starter_price = State()
    completion_time = State()

@user_router.message(IsUser(), CommandStart())
async def cmd_start(message: Message):
    user = await rq.get_user_data(message.from_user.id)
    if user.is_new:
        await message.answer("👋Привет, это бот Аукцион Saharok's/richa\n\n"
                                  "🕒Мы работаем: \n"
                                  "8:00 - 23:00мск, в это время вам ответят в течение 5 - 10 минут!\n\n"
                                  "📌Заказы, пришедшие с 23:00 до 8:00, будут выполнены утром, в порядке очереди.",
                         reply_markup=kb.main_menu)
        await rq.set_new_user(message.from_user.id)
    else:
        await message.answer(text='Выберете, что хотите сделать в меню',
                             reply_markup=kb.main_menu)

@user_router.message(IsUser(), Command('menu'))
async def menu(message: Message):
    await message.answer('Выберете, что хотите сделать в меню', reply_markup=kb.main_menu)

@user_router.message(IsUser(), F.text == "🪪Профиль")
async def profile(message: Message):
    user = await rq.get_user_data(message.from_user.id)
    await message.answer(f'👤 Имя пользователя:  {message.from_user.username} \n'
                         f'📍 Количество лотов:  {user.lots} \n'
                         f'💰 Ваш баланс:  {user.balance}⭐ \n',
                         reply_markup=kb.profile_menu)

@user_router.message(IsUser(), F.text == "🎫Создать лот")
async def create_lot(message: Message, state: FSMContext):
    await message.answer('📷 Пришлите фото подарка, который вы хотите выставить на продажу(владельца можно замазать). 🎁')
    await state.set_state(CreateLot.photo)

@user_router.message(IsUser(), F.text == "🛠️Тех. поддержка")
async def create_lot(message: Message):
    await message.answer('❓Если у вас возникли вопросы, то перейдите в нашего бота, чтобы обратиться в службу поддержки ✅',
                         reply_markup=kb.tech_bot_menu)

@user_router.message(IsUser(), F.text == "Вывести ⭐")
async def create_lot(message: Message):
    await message.answer('⚙ Для вывода звёзд, напишите в бот для вывода.',
                         reply_markup=kb.withdraw_bot_menu)

@user_router.message(IsUser(), F.photo, CreateLot.photo)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(CreateLot.starter_price)
    await message.answer('🌟 Введите  стартовую цену в звёздах, ⭐️=1,65₽.')

@user_router.message(IsUser(), CreateLot.starter_price)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(starter_price=int(message.text))
    await state.set_state(CreateLot.completion_time)
    await message.answer('🕒 Введите кол-во часов (от 1 до 24) через которое лот будет закрыт, если его не выкупят. 🕒')

@user_router.message(IsUser(), CreateLot.completion_time)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(hours=int(message.text))
    data = await state.get_data()
    await rq.set_lot(tg_id=message.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], photo_id=data['photo_id'])
    await message.answer_photo(photo=data['photo_id'],
                               caption=f'Стартовая цена: {data["starter_price"]}⭐\n'
                                       f'Время окончания: {data["hours"]}\n'
                                       f'Продавец: {message.from_user.username}\n'
                               )
    await message.answer('Ваш лот был отправлен на модерацию, после проверки он будет опубликован и вам прийдёт уведомление.')
    await state.clear()

@user_router.callback_query(IsUser(), F.data == 'deposit_balance')
async def deposit_balance(cb: CallbackQuery, state: FSMContext):
    await cb.answer('')
    await state.set_state(DepositBalance.number_stars)
    await cb.message.edit_text('✍ Введите кол-во звезд,на которое вы хотите пополнить свой баланс. 💰')

@user_router.message(IsUser(), DepositBalance.number_stars)
async def deposit_balance_s(message: Message, state: FSMContext):
    if message.text and message.text.isdigit() and int(message.text) >= 50 and int(message.text) <= 9000:
        await state.update_data(stars=int(message.text))
        data = await state.get_data()
        await message.answer(f'Сейчас мы пришлём счет, на пополнение баланса на {data["stars"]}⭐')
        await state.clear()
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title='Пополнение баланса.',
            description=f'Пополнение баланса профиля на {data["stars"]}⭐',
            provider_token=PAYMENTS_TOKEN,
            currency='rub',
            photo_url='https://digital-basket-01.wbbasket.ru/vol6/124/a0516b93ae5e8a32ac14e4fc265b575f/1280.jpg',
            photo_width=800,
            photo_height=650,
            photo_size=800,
            payload=f'deposit_balance_{data["stars"]}',
            prices=[types.LabeledPrice(label=f'Покупка {data["stars"]}⭐', amount=int(data['stars']*1.65*100))]
        )
    else:
        await message.answer("📌 Минимальное числовое значение 50, а максимальное 15 000 📌")

@user_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pcq: PreCheckoutQuery):
    await pcq.bot.answer_pre_checkout_query(pcq.id, ok=True)

@user_router.message(IsUser(), F.successful_payment)
async def process_suc_payment(message: Message):
    stars = int(message.successful_payment.invoice_payload.split('_')[-1])
    await rq.deposit_balance(tg_id=message.from_user.id, stars=stars)
    await message.answer(f"🎊 Вам успешно зачислено {stars}⭐️!")
