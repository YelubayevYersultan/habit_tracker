# 1. Базовый образ с установленным Python 3.11
FROM python:3.11-slim

# 2. Устанавливаем системные зависимости, необходимые для сборки некоторых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Создаем и переходим в рабочую директорию внутри контейнера
WORKDIR /app

# 4. Отключаем буферизацию логов Python (чтобы сразу видеть ошибки в терминале)
ENV PYTHONUNBUFFERED=1

# 5. Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копируем весь остальной код проекта в контейнер
COPY . .