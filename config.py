from dotenv import load_dotenv

import os

load_dotenv()

CHANNEL_ID = os.getenv('CHANNEL_ID')
TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')
PAYMENTS_TOKEN = os.getenv('PAYMENTS_TOKEN')
BOT_ID = os.getenv('BOT_ID')

status_mapping = {
    'SOLD': 'Продан',
    'EXPIRED': 'Истекло время',
    'TRADING': 'Идут торги',
}

TEXTS = {
    "cmd_start_auction_caption": "Стартовая цена: {starter_price}🌟\n"
                     "Последняя ставка: {real_price}🌟\n"
                     "Следующая минимальная ставка: {min_next_price}🌟\n"
                     "Блиц-цена: {moment_buy_price}🌟\n"
                     "Закончится: {expired_at} (MSK) ⏰\n"
                     "Продавец: {name} 👤\n",

    "cmd_start_msg": "👋 Привет, {name}! Это бот Telegram Gift Аукцион🎁\n\n"
                      "🕒 Мы работаем: \n"
                      "8:00 - 23:00 (МСК), в это время вам ответят в течение 5-10 минут! ⏳\n\n"
                      "📌 Заказы, пришедшие с 23:00 до 8:00, будут выполнены утром в порядке очереди. 📆",

    "main_menu_msg": "Выберите действие в меню 🛠",

    "user_profile_msg": "👤 Имя пользователя: {username} \n"
                        "📍 Количество лотов: {lots} \n"
                        "💰 Ваш баланс: {balance}🌟 \n",

    "support_msg": "❓ Если у вас возникли вопросы, перейдите в нашего бота для обращения в службу поддержки ✅",

    "withdraw_stars_msg": "⚙ Для вывода звёзд напишите в бот для вывода 💰",

    "create_lot_1_msg": "📷 Пришлите фото подарка, который вы хотите выставить на продажу (владельца можно замазать) 🎁\n"
                        "🔁 Если вы нажали кнопку случайно, нажмите «Прервать» 🔁",

    "create_lot_2_msg": "🌟 Введите стартовую цену в звёздах, 🌟️ = 1,65₽ 💸",

    "create_lot_3_msg": "🌟 Введите блиц-цену в звёздах (цена для моментального выкупа лота), 🌟️ = 1,65₽ 💸",
    "create_lot_3.2_msg": "🌟 Введите числовое значение, большее стартовой цены 🔢",

    "create_lot_end_msg": "Стартовая цена: {starter_price}🌟\n"
                      "Блиц-цена: {blitz_price}🌟\n"
                      "Длительность лота (в часах): {hours} ⏳\n"
                      "Продавец: {name} 👤\n",

    "create_lot_end_notif_msg": "📝 Ваш лот отправлен на модерацию. После проверки мы опубликуем его, и вам придёт уведомление! 📝",

    "deposit_balance_msg": "✍ Введите количество звёзд для пополнения баланса 💰\n"
                           "🔁 Если вы нажали кнопку случайно, нажмите «Прервать» 🔁",

    "send_deposit_balance_msg": "Сейчас мы пришлём счёт на пополнение баланса на {stars}🌟 💳",

    "limitations_deposit_balance_msg": "📌 Минимальное значение — 50, максимальное — 15 000 📌",

    "successful_payment": "🎊 Вам успешно зачислено {stars}🌟!",

    "interrupt_work_msg": "Вы прервали работу! ⛔",

    "lot_sold_msg": "Лот уже выкуплен. ✅",

    "lot_expired_msg": "Лот был закрыт по времени — его никто не купил. ⌛",

    "not_enough_stars": "💰 На вашем балансе недостаточно звёзд ⭐. Пополните баланс, нажав на кнопку ниже ⬇️",

    "you_are_seller_msg": "Вы не можете делать ставки на свой собственный лот. ⚠️",

    "bet_is_already_yours_msg": "⌛ Вы уже сделали ставку на этот лот. Дождитесь, пока её перебьют, или купите мгновенно ⌛️",

    "user_buy_lot_msg": "Вы выкупили лот #{id} за {moment_buy_price}🌟. В течение часа @{username} должен отправить вам подарок. 🎁",

    "seller_send_gift_msg": "Ваш лот #{id} закончился. Победитель — @{username}. В течение часа вы должны отправить подарок. "
                            "Если вы этого не сделаете, покупатель может открыть спор и вернуть звёзды, а вас забанят! ⚠️",

    "seller_expired_lot_msg": "Ваш лот #{id} закончился. На него никто не сделал ставок. ⌛",

    "sold_lot_caption": "Лот: <b>#{id}</b>\n"
                        "Стартовая цена: <b>{starter_price}</b>🌟\n"
                        "Последняя ставка: <b>{moment_buy_price}</b>🌟\n"
                        "Продавец: <b>{name}</b> 👤\n"
                        "Статус: <b>{status}</b> ✅\n"
                        "Покупатель: <b>{name}</b> 👤",

    "expired_lot_caption": "Лот: <b>#{id}</b>\n"
                        "Стартовая цена: <b>{starter_price}</b>🌟\n"
                        "Продавец: <b>{name}</b> 👤\n"
                        "Статус: <b>{status}</b> ⌛\n",

    "bid_exceeded_msg": "Ваша ставка на лот #{id} была перебита! Средства возвращены на баланс. 💰",

    "successful_bid_msg": "Вы успешно сделали ставку! ✅",

    "update_lot_after_bid_caption": "Лот: <b>#{id}</b>\n"
                                    "Стартовая цена: <b>{starter_price}</b>🌟\n"
                                    "Последняя ставка: <b>{real_price}</b>🌟\n"
                                    "Следующая минимальная ставка: <b>{min_next_price}</b>🌟\n"
                                    "Цена моментальной покупки: <b>{moment_buy_price}</b>🌟\n"
                                    "Продавец: <b>{name}</b> 👤\n"
                                    "Время окончания: <b>{expired_at}</b> (MSK) ⏰\n"
                                    "Статус: <b>{status}</b>",

    "username_missing_msg": "Извините, но у вас отсутствует username. Для использования бота создайте username и повторите команду. ⚠️",

    "you_are_banned_msg": "Похоже, вы забанены. Если считаете, что бан был ошибочным, обратитесь в техподдержку. ⚠️",

    "you_win_lot": "Ваша ставка на лот #{id} победила! В течение часа @{username} должен отправить вам подарок. "
                   "Если этого не случится, откройте спор. 🎉",

    "tech_channel_msg": "⁉️ Перейдите в чат техподдержки, чтобы посмотреть вопросы других пользователей ⁉️",

    "banned_list_msg": "Список забаненных пользователей: 🚫",

    "banned_list_msg_empty_msg": "Список пуст. ✅",

    "send_user_username_msg": "🧑‍💻 Введите username пользователя (без @).",

    "can't_see_admin_account_msg": "❌ Вы не можете просматривать профили администраторов ❌",

    "successful_ban_msg": "Пользователь успешно забанен. ✅",

    "send_ban_msg": "🚫 Вы были забанены 🚫\nЕсли это произошло по ошибке, обратитесь в техподдержку. ❗️",

    "successful_unban_msg": "Пользователь успешно разбанен. ✅",

    "send_unban_msg": "❗️ Вы были разбанены ❗️\n⚠️ Повторные нарушения могут привести к перманентному бану! Советуем соблюдать правила.",

    "see_new_lots_caption": "Лот: <b>#{id}</b>\n"
                        "Стартовая цена: <b>{starter_price}</b>🌟\n"
                        "Последняя ставка: <b>{real_price}</b>🌟\n"
                        "Следующая минимальная ставка: <b>{min_next_price}</b>🌟\n"
                        "Цена моментальной покупки: <b>{moment_buy_price}</b>🌟\n"
                        "Продавец: <b>{name}</b> 👤\n"
                        "Время окончания: <b>{expired_at}</b> (MSK) ⏰\n",

    "send_new_lot_caption": "Лот: <b>#{id}</b>\n"
                            "Стартовая цена: <b>{starter_price}</b>🌟\n"
                            "Следующая минимальная ставка: <b>{min_next_price}</b>🌟\n"
                            "Цена моментальной покупки: <b>{moment_buy_price}</b>🌟\n"
                            "Продавец: <b>{name}</b> 👤\n"
                            "Время окончания: <b>{expired_at}</b> (MSK) ⏰\n"
                            "Статус: <b>{status}</b>",

    "send_approve_lot_notif": "✅ Ваш лот был одобрен и выставлен на продажу!\n"
                              "🔗 Ссылка на ваш лот: https://t.me/{CHANNEL_ID}/{message_id}",

    "no_new_lots_msg": "🎉 Все лоты рассмотрены! Новых лотов нет.",

    "send_reject_lot_notif": "Ваш лот #{id} был отклонён. За подробностями обращайтесь в техподдержку. ❌",

    "reviewed_all_lots_before_this_msg": "Вы рассмотрели все лоты перед данным. ✅",

    "reviewed_all_lots_after_this_msg": "Вы рассмотрели все лоты после данного. ✅",

    "end_moderation_msg": "Вы закончили модерировать лоты. ✅",

    "moment_price_men_real_price": "Реальная цена превышает цену моментальной покупки, вы не можете выкупить этот лот."
}
