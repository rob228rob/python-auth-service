# app/main.py
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings

from app.kafka.kafka_producer import send_message
from app.database.models import Base
from app.database import engine
from app.auth_router import router as auth_router
from app.history_router import history_router


Base.metadata.create_all(bind=engine)

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(history_router, prefix="/history", tags=["history"])

app.add_middleware(SessionMiddleware, secret_key=settings.yandex_client_secret)

logger = logging.getLogger(__name__)

@app.get("/health")
def healthcheck():
    # send_message(topic=settings.notify_topic, key="health", message={"username":"mock", "message":"Healthy"})
    # logger.info(f"sending msg to topic: ${settings.notify_topic}")
    return {
        "status" : 200,
        "msg": "Приложение запущено"
    }
