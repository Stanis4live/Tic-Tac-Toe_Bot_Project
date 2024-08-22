FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY pyproject.toml poetry.lock /app/

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Копируем все файлы проекта
COPY . /app/

# Добавляем папку проекта в PYTHONPATH, чтобы модули были видимы
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "bot/main.py"]
