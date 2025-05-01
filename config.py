from dotenv import load_dotenv

import os

load_dotenv()

CHANNEL_ID = os.getenv('CHANNEL_ID')
TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')
PAYMENTS_TOKEN = os.getenv('PAYMENTS_TOKEN')
BOT_ID = os.getenv('BOT_ID')
YOO_TOKEN = os.getenv('YOO_TOKEN')
SECRET_KEY = os.getenv('SECRET_KEY')

status_mapping = {
    'SOLD': 'Продан',
    'EXPIRED': 'Истекло время',
    'TRADING': 'Идут торги',
}

TEXTS = {
    "cmd_start_auction_caption": "📦 Стартовая цена: {starter_price}🌟\n"
                             "💰 Последняя ставка: {real_price}🌟\n"
                             "➡️ Минимальная следующая ставка: {min_next_price}🌟\n"
                             "🚀 Блиц-цена: {moment_buy_price}🌟\n"
                             "⏰ Завершение: {expired_at} (МСК)\n"
                             "👤 Продавец: {name}\n",

    "cmd_start_msg": "👋 Привет, {name}! Добро пожаловать в Telegram Gift Аукцион 🎁\n\n"
                     "🕒 Мы онлайн с 8:00 до 23:00 (МСК). Обычно отвечаем в течение 5–10 минут!\n\n"
                     "🌙 Заявки после 23:00 обрабатываются утром, в порядке очереди. Спасибо за понимание!",

    "main_menu_msg": "🔍 Выберите действие из меню ниже:",

    "user_profile_msg": "👤 Ваш профиль:\n"
                        "📛 Имя пользователя: {username}\n"
                        "📦 Количество лотов: {lots}\n"
                        "💰 Баланс: {balance}🌟\n",

    "support_msg": "📩 Нужна помощь? Напишите нам через бота поддержки ✅",

    "withdraw_stars_msg": "💸 Хотите вывести звёзды? Нажмите на кнопку ниже и следуйте инструкции!",

    "create_lot_1_msg": "📷 Пришлите фото подарка, который хотите выставить на продажу.\n"
                        "👀 Лицо владельца можно замазать.\n"
                        "❌ Если передумали, нажмите «Отменить».",

    "create_lot_2_msg": "💰 Укажите стартовую цену в звёздах.\n"
                        "📌 1🌟 = 1,65₽",

    "create_lot_3_msg": "🚀 Укажите блиц-цену (для моментального выкупа).\n"
                        "📌 1🌟 = 1,65₽",

    "create_lot_3.2_msg": "⚠️ Введите значение, большее стартовой цены:",

    "create_lot_4_msg": "🕒 Выберите длительность лота (в часах):",

    "create_lot_end_caption": "📦 Стартовая цена: {starter_price}🌟\n"
                              "🚀 Блиц-цена: {blitz_price}🌟\n"
                              "⏰ Длительность: {hours} ч.\n"
                              "👤 Продавец: {name}\n",

    "create_lot_end_notif_msg": "📝 Лот отправлен на модерацию. Мы проверим его и сообщим, как только он появится на аукционе!",

    "deposit_balance_msg": "💳 Введите количество звёзд для пополнения:\n"
                           "❌ Для отмены — нажмите «Отменить».",

    "send_deposit_balance_msg": "📨 Мы готовим счёт на пополнение на {stars}🌟.",

    "limitations_deposit_balance_msg": "📌 Пополнение от 50 до 15 000 звёзд.",

    "successful_payment": "🎉 Успешное пополнение на {stars}🌟! Спасибо!",

    "interrupt_work_msg": "🚫 Вы прервали текущую операцию.",

    "lot_sold_msg": "✅ Лот уже выкуплен другим участником.",

    "lot_expired_msg": "⌛ Время продажи лота истекло. Он не был выкуплен.",

    "not_enough_stars": "❗ У вас недостаточно звёзд. Пополните баланс через кнопку ниже ⬇️",

    "you_are_seller_msg": "⚠️ Вы не можете делать ставки на собственный лот.",

    "bet_is_already_yours_msg": "⌛ Вы уже сделали ставку. Дождитесь перебития или купите лот мгновенно.",

    "user_buy_lot_msg": "🎁 Вы выкупили лот #{id} за {moment_buy_price}🌟! @{username} отправит вам подарок в течение часа.",

    "seller_send_gift_msg": "📦 Ваш лот #{id} продан. Победитель — @{username}.\n"
                            "⏳ У вас 1 час на отправку подарка. Неотправка может привести к блокировке!",

    "seller_expired_lot_msg": "📦 Ваш лот #{id} завершился без ставок.",

    "sold_lot_caption": "🎁 Лот: <b>#{id}</b>\n"
                        "💵 Старт: <b>{starter_price}</b>🌟\n"
                        "💰 Финал: <b>{moment_buy_price}</b>🌟\n"
                        "👤 Продавец: <b>{seller}</b>\n"
                        "✅ Статус: <b>{status}</b>\n"
                        "🧑 Покупатель: <b>{name}</b>",

    "expired_lot_caption": "📦 Лот: <b>#{id}</b>\n"
                            "💵 Старт: <b>{starter_price}</b>🌟\n"
                            "👤 Продавец: <b>{name}</b>\n"
                            "⌛ Статус: <b>{status}</b>",

    "bid_exceeded_msg": "📉 Ваша ставка на лот #{id} была перебита. Средства возвращены на баланс.",

    "successful_bid_msg": "✅ Ставка успешно размещена!",

    "update_lot_after_bid_caption": "🎯 Лот: <b>#{id}</b>\n"
                                    "💵 Старт: <b>{starter_price}</b>🌟\n"
                                    "🔄 Последняя ставка: <b>{real_price}</b>🌟\n"
                                    "➡️ Следующая ставка: <b>{min_next_price}</b>🌟\n"
                                    "🚀 Блиц: <b>{moment_buy_price}</b>🌟\n"
                                    "👤 Продавец: <b>{name}</b>\n"
                                    "⏰ Завершение: <b>{expired_at}</b> (МСК)\n"
                                    "📌 Статус: <b>{status}</b>",

    "username_missing_msg": "⚠️ У вас отсутствует username. Установите его в настройках Telegram и повторите команду.",

    "you_are_banned_msg": "🚫 Вы были забанены. Если это ошибка — обратитесь в поддержку.",

    "you_win_lot": "🎉 Ваша ставка на лот #{id} победила! @{username} должен отправить подарок в течение часа.",

    "tech_channel_msg": "🔧 Перейдите в тех. канал, чтобы увидеть ответы на часто задаваемые вопросы.",

    "banned_list_msg": "🚫 Список забаненных пользователей:",

    "banned_list_msg_empty_msg": "✅ Список пуст.",

    "send_user_username_msg": "✍ Введите username пользователя (без @):",

    "can't_see_admin_account_msg": "❌ Просмотр профиля администратора недоступен.",

    "successful_ban_msg": "✅ Пользователь успешно забанен.",

    "send_ban_msg": "🚫 Вы были забанены. Если это ошибка — обратитесь в поддержку.",

    "successful_unban_msg": "✅ Пользователь успешно разбанен.",

    "send_unban_msg": "⚠️ Вы были разбанены. Повторные нарушения могут привести к пожизненному бану.",

    "see_new_lots_caption": "🆕 Лот: <b>#{id}</b>\n"
                            "💵 Старт: <b>{starter_price}</b>🌟\n"
                            "🔄 Ставка: <b>{real_price}</b>🌟\n"
                            "➡️ Следующая: <b>{min_next_price}</b>🌟\n"
                            "🚀 Блиц: <b>{moment_buy_price}</b>🌟\n"
                            "👤 Продавец: <b>{name}</b>\n"
                            "⏰ Завершение: <b>{expired_at}</b> (МСК)",

    "send_new_lot_caption": "📦 Лот: <b>#{id}</b>\n"
                             "💵 Старт: <b>{starter_price}</b>🌟\n"
                             "➡️ Следующая: <b>{min_next_price}</b>🌟\n"
                             "🚀 Блиц: <b>{moment_buy_price}</b>🌟\n"
                             "👤 Продавец: <b>{name}</b>\n"
                             "⏰ Завершение: <b>{expired_at}</b> (МСК)\n"
                             "📌 Статус: <b>{status}</b>",

    "send_approve_lot_notif": "✅ Ваш лот одобрен и опубликован!\n"
                               "🔗 Ссылка: https://t.me/{CHANNEL_ID}/{message_id}",

    "no_new_lots_msg": "🎉 Все лоты проверены. Новых нет!",

    "send_reject_lot_notif": "❌ Ваш лот #{id} отклонён. Обратитесь в поддержку за деталями.",

    "reviewed_all_lots_before_this_msg": "✅ Все предыдущие лоты просмотрены.",

    "reviewed_all_lots_after_this_msg": "✅ Все последующие лоты просмотрены.",

    "end_moderation_msg": "🛑 Вы завершили модерацию лотов.",

    "moment_price_men_real_price": "❗ Нельзя выкупить лот: ставка выше блиц-цены."
}

