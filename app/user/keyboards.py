from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎫Создать лот')],
    [KeyboardButton(text='🪪Профиль'),KeyboardButton(text='Вывести ⭐'), KeyboardButton(text='🛠️Тех. поддержка')] #KeyboardButton(text='📜Ваши Лоты'),
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')

profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Пополнить баланс.',
                          callback_data='deposit_balance')]
])

tech_bot_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Написать в тех. поддержку ⚙',
                          url='https://t.me/auction_saharok_bot?start=auction_saharok_bot')]
])
withdraw_bot_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вывести звезды ⚙',
                          url='https://t.me/auction_saharok_bot?start=auction_saharok_bot')]
])