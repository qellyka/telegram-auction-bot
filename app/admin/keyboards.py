from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎫Посмотреть новые лоты')],
    [KeyboardButton(text='🪪Управлениями пользователями'),KeyboardButton(text="📜Управлениями лотами"), KeyboardButton(text='🛠️Вопросы пользователей',)],
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')

