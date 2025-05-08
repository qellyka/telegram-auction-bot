from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📥 Новые лоты на модерации"), KeyboardButton(text="📝 Заявки на вывод средств")],
    [KeyboardButton(text="🧑‍💼 Пользователи"), KeyboardButton(text="🛑 Чёрный список")],
    [KeyboardButton(text="⚖️ Споры",)]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню")

tech_channel_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти в канал", url="https://t.me/+szBkT23ZFP1lMWQy")]])


tech_bot_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Написать в тех. поддержку ⚙",
                          url="https://t.me/auction_saharok_bot?start=auction_saharok_bot")]
])

choose_user = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Продавец",
                          callback_data="find_seller"),
     InlineKeyboardButton(text="Текущий участник",
                          callback_data="find_applicant")]
])

interrupt_work = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Прервать",
                          callback_data="interrupt_work")]
])
