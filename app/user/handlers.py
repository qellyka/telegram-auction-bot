import types

from aiogram import F, Router, types

from aiogram.filters import CommandStart
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


# Работа с меню


@user_router.message(IsUser(), CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет!',
                         reply_markup=kb.main_menu)

@user_router.message(IsUser(), F.text == "🪪Профиль")
async def profile(message: Message):
    user = await rq.get_user_data(message.from_user.id)
    await message.answer(f'Профиль:  {message.from_user.username} \n'
                         f'Количество лотов:  {user.lots} \n'
                         f'Баланс:  {user.balance}⭐ \n',
                         reply_markup=kb.profile_menu)

@user_router.message(IsUser(), F.text == "🎫Создать лот")
async def create_lot(message: Message, state: FSMContext):
    await message.answer('Отправьте фотографию подарка, который вы выставляете на продажу.')
    await state.set_state(CreateLot.photo)

@user_router.message(IsUser(), F.text == "🛠️Тех. поддержка")
async def create_lot(message: Message):
    await message.answer('Чтобы обратиться в службу поддержки напишите перейдите в нашего бота.',
                         reply_markup=kb.tech_bot_menu)

@user_router.message(IsUser(), F.text == "Вывести ⭐")
async def create_lot(message: Message):
    await message.answer('Если вы хотите вывести звезды, то напишите в поддержку.',
                         reply_markup=kb.tech_bot_menu)


# Созданние лота


@user_router.message(IsUser(), F.photo, CreateLot.photo)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(CreateLot.starter_price)
    await message.answer('Теперь введите пожалуйста стартовую цену в ⭐(1.65руб).')

@user_router.message(IsUser(), CreateLot.starter_price)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(starter_price=int(message.text))
    await state.set_state(CreateLot.completion_time)
    await message.answer('Теперь введите цифру, от 1 до 24 - кол-во часов через которое лот будет закрыт, если его никто не выкупил.')

@user_router.message(IsUser(), CreateLot.completion_time)
async def set_lots_photo(message: Message, state: FSMContext):
    await state.update_data(hours=int(message.text))
    data = await state.get_data()
    await rq.set_lot(tg_id=message.from_user.id, starter_price=data['starter_price'], hours_exp=data['hours'], photo_id=data['photo_id'])
    await message.answer('Ваш лот был успешно добавлен!')
    await state.clear()


# Пополнение баланса


@user_router.callback_query(IsUser(), F.data == 'deposit_balance')
async def deposit_balance(cb: CallbackQuery, state: FSMContext):
    await cb.answer('')
    await state.set_state(DepositBalance.number_stars)
    await cb.message.edit_text('Введите на какое количество здвезд вы хотите пополнить сво баланс. Минимальное кол-во звезд - 50⭐, максимальное - 9000⭐.')

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
        await message.answer("Пожалуйста отправьте числовое значение, например 100.")

@user_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pcq: PreCheckoutQuery):
    await pcq.bot.answer_pre_checkout_query(pcq.id, ok=True)

@user_router.message(IsUser(), F.successful_payment)
async def process_suc_payment(message: Message):
    stars = int(message.successful_payment.invoice_payload.split('_')[-1])
    await rq.deposit_balance(tg_id=message.from_user.id, stars=stars)
    await message.answer(f"Вам успешно зачисленны {stars}⭐")
