import hashlib
import logging
import asyncio
import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.memory import MemoryStorage

from fastapi import FastAPI, Request, status, HTTPException

from app.admin.handlers import admin_router
from app.user.handlers import user_router
from app.auction.functions import background_tasks
from app.db.engine import setup_db # импорт функции для обработки

from config import TOKEN, TELEGRAM_WEBHOOK_PATH, YOOMONEY_WEBHOOK_PATH, YOO_SECRET

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

@app.post(TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(update: dict):
    try:
        telegram_update = Update.model_validate(update)
        await dp.feed_update(bot, telegram_update)
    except Exception as e:
        logging.exception("Telegram webhook error: %s", e)
    return {"ok": True}

@app.post(YOOMONEY_WEBHOOK_PATH)
async def yoomoney_webhook(request: Request):
    form = await request.form()
    data = dict(form)

    label = data.get("label", "")
    amount = data.get("amount", "")
    notification_type = data.get("notification_type", "")
    operation_id = data.get("operation_id", "")
    datetime = data.get("datetime", "")
    sender = data.get("sender", "")
    codepro = data.get("codepro", "")
    sha1_hash = data.get("sha1_hash", "")
    secret = YOO_SECRET

    base_string = "&".join([notification_type, operation_id, amount, currency := "643",
                            datetime, sender, codepro, secret, label])

    check_hash = hashlib.sha1(base_string.encode("utf-8")).hexdigest()

    if sha1_hash != check_hash:
        raise HTTPException(status_code=400, detail="Invalid signature")

    print(f"💸 Пользователь оплатил {amount} RUB (label: {label})")

    from app.db.requests import deposit_balance
    await deposit_balance(tg_id=int(label), stars=int(float(amount)))

    try:
        await bot.send_message(chat_id=int(label), text=f"✅ Вы успешно пополнили баланс на {amount}₽!")
    except Exception as e:
        print(f"❗ Ошибка отправки сообщения: {e}")

    return {"ok": True}

# Telegram bot init
async def on_startup():
    await setup_db()
    dp.include_router(user_router)
    dp.include_router(admin_router)
    asyncio.create_task(background_tasks(bot=bot))

@app.on_event("startup")
async def startup():
    await on_startup()

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
