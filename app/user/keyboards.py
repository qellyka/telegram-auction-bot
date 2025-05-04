from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎫Создать лот"), KeyboardButton(text="📊 Мои аукционы")],
    [KeyboardButton(text="👨‍👩‍👧‍👦Реферальная программа")],
    [KeyboardButton(text="🪪Профиль"),KeyboardButton(text="Вывести 🌟"), KeyboardButton(text="🛠️Тех. поддержка")]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню")

auction_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🔹 Мои лоты"), KeyboardButton(text="🔹 Мои ставки")],
],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню")

user_auction_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои лоты", callback_data="my_lots")],
    [InlineKeyboardButton(text="📈 Мои ставки", callback_data="my_bids")],
    [InlineKeyboardButton(text="⭐ Избранные", callback_data="my_favorites")],
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
])

banks_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🟡 Тинькофф", callback_data="tinkoff")],
    [InlineKeyboardButton(text="🟢 Сбербанк", callback_data="sberbank")],
    [InlineKeyboardButton(text="🔴 Альфа-Банк", callback_data="alfabank")],
    [InlineKeyboardButton(text="⭐ Звезды", callback_data="stars")]
])

withdraw_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="send_withdraw_blank")],
    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_withdraw_blank")],
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
    [InlineKeyboardButton(text="Продолжить",
                          callback_data="withdraw_stars")],
    [InlineKeyboardButton(text="Отменить",
                          callback_data="interrupt_work")]
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