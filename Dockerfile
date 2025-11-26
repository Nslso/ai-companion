FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Создание директорий для данных
RUN mkdir -p chroma_db data

# Экспорт порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "src/main.py"]