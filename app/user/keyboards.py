from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎫Создать лот"), KeyboardButton(text="📊 Мои аукционы")],
    [KeyboardButton(text="👨‍👩‍👧‍👦Реферальная программа")],
    [KeyboardButton(text="🪪Профиль"),KeyboardButton(text="Вывести ⭐"), KeyboardButton(text="🛠️Тех. поддержка")]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню")

user_auction_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои лоты", callback_data="my_lots")],
    [InlineKeyboardButton(text="📈 Мои ставки", callback_data="my_bids")],
    [InlineKeyboardButton(text="⭐ Избранные", callback_data="my_favorites")],
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
])


profile_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Пополнить баланс",
                          callback_data="deposit_balance")]
])

tech_bot_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Написать в тех. поддержку ⚙",
                          url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
])
withdraw_bot_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Вывести звезды ⚙",
                          url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
])

lot_times_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1",
                          callback_data="one_hour"),
     InlineKeyboardButton(text="2",
                          callback_data="two_hour"),
    InlineKeyboardButton(text="4",
                          callback_data="four_hour"),
    InlineKeyboardButton(text="8",
                          callback_data="eight_hour")
     ],
    [InlineKeyboardButton(text="10",
                          callback_data="ten_hour"),
     InlineKeyboardButton(text="12",
                          callback_data="twelve_hour"),
    InlineKeyboardButton(text="24",
                          callback_data="twenty_four_hour"),
    InlineKeyboardButton(text="48",
                          callback_data="forty_eight_hour")
     ]
])

interrupt_work = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отменить",
                          callback_data="interrupt_work")]
])