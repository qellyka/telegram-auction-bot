# Telegram Auction Bot 🎁

A Telegram bot for conducting auctions, specializing in the sale of Telegram gifts and other exclusive items between users.

## 📋 Project Description

Telegram Auction Bot is a platform that allows users to create auctions and list items for sale. The main focus of the bot is on Telegram gifts (stickers, premium subscriptions, and other digital goods from the Telegram platform), but it can be used for other items as well.

### Main Features:
- Creating auctions with various settings (start/end time, starting price)
- Listing lots with descriptions and photos
- Bidding system with notifications
- Auction and transaction history
- User ratings
- Filtering and searching by lot categories

## 🛠️ Technologies

- **Python 3.9+**
- **aiogram 3.x** - asynchronous framework for Telegram Bot API
- **SQLAlchemy 2.0** - ORM for database operations
- **asyncpg** - asynchronous PostgreSQL driver
- **PostgreSQL** - database management system
- **Poetry** - dependency and virtual environment management

## 📦 Installation and Launch

### Prerequisites

- Python 3.9 or higher
- PostgreSQL
- Poetry

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/auction-bot.git
cd auction-bot
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a config.py file based on example_config.py:
```bash
cp example_config.py config.py
```

### Launch

```bash
poetry run python -m app.bot
```

## 🧩 Project Structure

```
auction-bot/
├── app/
│   ├── admin/
│   │   ├── handlers.py     # Admin command handlers
│   │   └── keyboards.py    # Admin keyboards
│   ├── db/
│   │   ├── engine.py       # Database connection setup
│   │   ├── models.py       # Data models
│   │   └── requests.py     # Database operation functions
│   ├── user/
│   │   ├── handlers.py     # User command handlers
│   │   ├── keyboards.py    # User keyboards
│   │   ├── filters.py      # Message filters
│   │   └── middlewares.py  # Middleware handlers
│   ├── bot.py              # Main bot file
│   └── config.py           # Bot configuration
├── example_config.py       # Configuration example
├── pyproject.toml          # Poetry configuration
└── poetry.lock             # Project dependencies
```

## 📄 License

MIT License

## 👨‍💻 Authors

### - [qellyka](https://github.com/qellyka)

---

If you have questions or suggestions, please create an Issue or contact us via Telegram: [qellyka](https://t.me/qellyka)