from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎫Новые лоты')],
    [KeyboardButton(text='🪪Управлениями пользователями'),KeyboardButton(text="📜Управлениями лотами"), KeyboardButton(text='🛠️Вопросы пользователей',
                                                                                                                   url='https://t.me/+szBkT23ZFP1lMWQy')],
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')
