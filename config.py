from dotenv import load_dotenv

import os

load_dotenv()

CHANNEL_ID = os.getenv('CHANNEL_ID')
TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')
PAYMENTS_TOKEN = os.getenv('PAYMENTS_TOKEN')