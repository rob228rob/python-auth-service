# app/jwt_service
import logging

from fastapi import HTTPException, Request

from app.config import settings
from app.kafka.kafka_producer import send_message
from app.database.models import User


logger = logging.getLogger(__name__)

def build_token_payload(user: User) -> dict:
    return {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.name if user.role else "user",
        "email": user.email,
        "iss": "auth-service"
    }


def send_registration_notification(user: User, provider: str = None):
    if provider:
        message_text = f"Добро пожаловать через {provider}!"
    else:
        message_text = "Добро пожаловать!"
    message = {
        "user_id": user.id,
        "username": user.username,
        "message": message_text
    }
    try:
        send_message(
            key=str(message.get("user_id", "none")),
            message=message,
            topic=settings.notify_topic)
    except Exception as e:
        logger.error(f"Ошибка при отправке Kafka-сообщения: {e}")


def build_token_response(user: User, access_token: str, refresh_token: str) -> dict:
    access_expires_in = settings.access_token_expire_minutes * 60
    # refresh_token установлен на 7 дней
    refresh_expires_in = settings.refresh_token_expire_days * 24 * 3600
    return {
        "access_token": access_token,
        "expires_in": access_expires_in,
        "refresh_expires_in": refresh_expires_in,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "not-before-policy": 0,
        "scope": "email"
    }


def build_access_token(access_token: str) -> dict:
    access_expires_in = settings.access_token_expire_minutes * 60
    return {
        "access_token": access_token,
        "expires_in": access_expires_in,
        "token_type": "Bearer"
    }
