# docker/Dockerfile.app
FROM python:3.9-slim

WORKDIR /app

# Копируем исходники основного сервиса
COPY ./app /app/app
COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
