# app/auth_router.py
import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth_service import send_registration_notification, build_token_payload, build_token_response, \
    build_access_token
from app.config import settings
from app.database.db_service import create_new_user, save_login_attempt_to_db, get_or_create_oauth_user, \
    get_existing_user, get_db, pwd_context
from app.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_token, get_payload,
)
from app.database.models import User
from app.oauth_utils import get_oauth_user_info

logger = logging.getLogger(__name__)

router = APIRouter()


oauth = OAuth()
oauth.register(
    name='yandex',
    client_id=settings.yandex_client_id,
    client_secret=settings.yandex_client_secret,
    authorize_url="https://oauth.yandex.ru/authorize",
    token_endpoint="https://oauth.yandex.ru/token",
    client_kwargs={'scope': 'login:email login:info'}
)
oauth.register(
    name='vk',
    client_id=settings.vk_client_id,
    client_secret=settings.vk_client_secret,
    token_endpoint=settings.vk_token_endpoint,
    api_base_url=settings.vk_api_base_url,
    authorize_url=settings.vk_authorize_url,
    client_kwargs={'scope': 'email,offline'},
)


# dtos

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenRefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    logger.info(f"Начало регистрации пользователя с email: {user.email}")
    try:
        if get_existing_user(db, user.email):
            logger.warning(f"Регистрация: Пользователь с email {user.email} уже существует")
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

        new_user = create_new_user(db, user.username, user.email, user.password)
        logger.info(f"Создан новый пользователь с ID: {new_user.id}")

        send_registration_notification(new_user)
        logger.info(f"Отправлено уведомление о регистрации для пользователя {new_user.id}")

        token_payload = build_token_payload(new_user)
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        logger.info(f"Сгенерированы токены для пользователя {new_user.id}")

        response = build_token_response(new_user, access_token, refresh_token)
        logger.info(f"Регистрация успешно завершена для пользователя {new_user.id}")
        return response
    except Exception as e:
        logger.error(f"Ошибка в эндпоинте /register: {e}", exc_info=True)
        raise


@router.post("/login")
def normal_login(user: UserLogin, db: Session = Depends(get_db), request: Request = None):
    logger.info(f"Попытка входа для email: {user.email}")
    existing_user = db.query(User).filter(User.email == user.email).first()
    if not existing_user:
        logger.warning(f"Логин: Пользователь с email {user.email} не найден")
        raise HTTPException(status_code=400, detail="Неверный email или пароль")
    if not pwd_context.verify(user.password, existing_user.hashed_password):
        logger.warning(f"Логин: Неверный пароль для пользователя с email {user.email}")
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    ip_address = request.client.host if request and request.client else None
    save_login_attempt_to_db(existing_user, db, ip_address)
    token_payload = build_token_payload(existing_user)
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    return build_token_response(existing_user, access_token, refresh_token)


@router.post("/token/refresh")
def refresh_tokens(data: TokenRefreshRequest, db: Session = Depends(get_db)):
    logger.info("Начало обновления токенов")
    try:
        payload = get_payload(data.refresh_token, "refresh")
        if payload is None:
            logger.warning("Обновление токенов: недействительный или просроченный refresh токен")
            raise HTTPException(status_code=401, detail="Неверный или просроченный refresh токен")
        user_id = payload.get("sub")
        user = db.query(User).get(user_id)
        if not user:
            logger.error(f"Обновление токенов: пользователь с ID {user_id} не найден")
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        new_payload = build_token_payload(user)
        new_access_token = create_access_token(new_payload)
        logger.info(f"Токен успешно обновлен для пользователя {user_id}")
        return build_access_token(new_access_token)
    except Exception as e:
        logger.error(f"Ошибка в эндпоинте /refresh: {e}", exc_info=True)
        raise

@router.get("/token/validate")
def validate_token(token: str = Query(...), token_type: str = Query("access")):
    verified = verify_token(token, token_type)
    if not verified:
        return {"active": False}
    payload = get_payload(token, token_type)
    return {
        "active": True,
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
        "sub": payload.get("sub"),
        "iss": payload.get("iss"),
        "email": payload.get("email"),
        "scope": payload.get("scope", "profile email")
    }

@router.get("/login/{provider}")
async def oauth_login(request: Request, provider: str):
    if provider not in ["yandex", "vk"]:
        raise HTTPException(status_code=400, detail="Неверный провайдер")
    redirect_uri = request.url_for("oauth_callback", provider=provider)
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/callback/{provider}", name="oauth_callback")
async def oauth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    if provider not in ["yandex", "vk"]:
        raise HTTPException(status_code=400, detail="Неверный провайдер")
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    if provider == "yandex":
        logger.info(f"Получен токен от Yandex: {token}")
    else:
        logger.info(f"Получен токен от VK: {token}")
    user_info = await get_oauth_user_info(provider, client, token)
    logger.info("User info: %s", user_info)
    user = get_or_create_oauth_user(db, provider, user_info)
    logger.info("User: %s", user)
    token_payload = build_token_payload(user)
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    return build_token_response(user, access_token, refresh_token)