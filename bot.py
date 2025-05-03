import os
import hashlib
import logging
import asyncio
import uvicorn

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.memory import MemoryStorage

from app.admin.handlers import admin_router
from app.user.handlers import user_router
from app.auction.functions import background_tasks
from app.db.engine import setup_db

from config import TOKEN, TELEGRAM_WEBHOOK_PATH, YOOMONEY_WEBHOOK_PATH, YOO_SECRET

WEBHOOK_URL = f"https://lotoro.ru{TELEGRAM_WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_db()
    dp.include_router(user_router)
    dp.include_router(admin_router)
    asyncio.create_task(background_tasks(bot))
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("🚀 Bot webhook set and background tasks started.")

    yield

    await bot.delete_webhook()
    logging.info("🛑 Bot webhook removed.")


app = FastAPI(lifespan=lifespan)


@app.post(TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"ok": True})
    except Exception as e:
        logging.exception("Error handling Telegram webhook:")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post(YOOMONEY_WEBHOOK_PATH)
async def yoomoney_webhook(request: Request):
    form = await request.form()
    data = dict(form)

    required_fields = [
        "notification_type", "operation_id", "amount", "currency",
        "datetime", "sender", "codepro", "sha1_hash"
    ]
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing required fields")

    label = data.get("label", "")
    signature_string = "&".join([
        data["notification_type"],
        data["operation_id"],
        data["amount"],
        data["currency"],
        data["datetime"],
        data["sender"],
        data["codepro"],
        YOO_SECRET,
        label
    ])
    calculated_hash = hashlib.sha1(signature_string.encode("utf-8")).hexdigest()

    if calculated_hash != data["sha1_hash"]:
        logging.warning(f"Invalid SHA1: expected {calculated_hash}, got {data['sha1_hash']}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logging.info(f"✅ YooMoney payment confirmed: {data}")
    return {"status": "ok"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("bot:app", host="0.0.0.0", port=8000)
