FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости отдельно (кэш Docker слоёв)
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Папка фото создаётся заранее, чтобы том Docker получил владельца app
RUN useradd --create-home app && mkdir -p /app/media && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
