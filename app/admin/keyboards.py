from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from app.admin.handlers import tech_channel

admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎫Посмотреть новые лоты')],
    [KeyboardButton(text='🪪Управлениями пользователями'),KeyboardButton(text="📜Управлениями лотами"), KeyboardButton(text='🛠️Вопросы пользователей',)],
],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню')

tech_channel_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Перейти в канал', url='https://t.me/+szBkT23ZFP1lMWQy')]])
