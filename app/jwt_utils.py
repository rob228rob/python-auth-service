# app/jwt_utils.py
import logging
from datetime import datetime, timedelta
from http.client import HTTPException

from jose import JWTError, jwt
from app.config import settings

logger = logging.getLogger(__name__)

def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
        "type": "access"
    })
    token = jwt.encode(to_encode, settings.jwt_access_secret, algorithm=settings.jwt_algorithm)
    logger.debug(f"Access token created: {token}")
    return token

def create_refresh_token(data: dict):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(days=7)
    to_encode.update({
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
        "type": "refresh"
    })
    token = jwt.encode(to_encode, settings.jwt_refresh_secret, algorithm=settings.jwt_algorithm)
    logger.debug(f"Refresh token created: {token}")
    return token

def get_payload(token: str, token_type: str = "access") -> dict:
    try:
        if token_type == "refresh":
            payload = jwt.decode(token, settings.jwt_refresh_secret, algorithms=[settings.jwt_algorithm])
        elif token_type == "access":
            payload = jwt.decode(token, settings.jwt_access_secret, algorithms=[settings.jwt_algorithm])
        logger.info(f"Decoded payload: {payload}")
    except Exception as e:
        payload = {"error" : f"{e}"}
    return payload


def verify_token(token: str, token_type: str) -> bool:
    logger.debug(f"Verifying token of type '{token_type}': {token}")
    try:
        payload = get_payload(token, token_type)
        logger.debug(f"Decoded payload: {payload}")

        # Проверка обязательных полей
        if payload.get("email") is None or payload.get("role") is None:
            logger.warning("Token validation failed: 'email' or 'role' field is missing.")

        exp = payload.get("exp")
        if exp is None:
            logger.warning("Token validation failed: 'exp' field is missing.")
            return False
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token validation failed: token has expired.")
            return False

        if payload.get("type") != token_type:
            logger.warning(f"Token validation failed: expected token type '{token_type}', got '{payload.get('type')}'.")
            return False

        logger.debug("Token validation successful.")
        return True
    except JWTError as e:
        logger.error(f"JWTError during token validation: {e}")
        return False

def verify_access_token(token: str) -> bool:
    return verify_token(token, "access")

def verify_refresh_token(token: str) -> bool:
    return verify_token(token, "refresh")
