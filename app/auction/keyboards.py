from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

trade_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Подтвердить отправку",
                          callback_data="accept_trade")],
    [InlineKeyboardButton(text="Открыть спор",
                          callback_data="open_issue")]
])

trade_seller_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Открыть спор",
                          callback_data="open_issue")]
])