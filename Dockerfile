# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем зависимости для Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry

# Создаём рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта (и Poetry конфигурацию)
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости проекта через Poetry
RUN poetry install --no-root

# Копируем весь код проекта
COPY . /app/

# Преобразуем зависимости для работы без виртуального окружения Poetry
RUN poetry config virtualenvs.create false

# Открываем порт, если необходимо (например, для webhook или других нужд)
#EXPOSE 8080

# Команда для запуска бота
CMD ["poetry", "run", "python", "bot.py"]
