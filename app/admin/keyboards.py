from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🎫Посмотреть новые лоты")],
    [KeyboardButton(text="🪪Управление пользователями"),KeyboardButton(text="📜Управление лотами")],
    [KeyboardButton(text="🛠️Вопросы пользователей",), KeyboardButton(text="🃏Черный список",)]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню")

tech_channel_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти в канал", url="https://t.me/+szBkT23ZFP1lMWQy")]])


tech_bot_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Написать в тех. поддержку ⚙",
                          url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
])

interrupt_work = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Прервать",
                          callback_data="interrupt_work")]
])
