import logging
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


async def fetch_yandex_user_info(client, access_token: str) -> dict:
    """меняем токен на инфу о юзере"""
    resp = await client.get(
        settings.yandex_oauth_user_info_url,
        params={"format": "json"},
        token={"access_token": access_token}
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=resp.status_code, detail=f"Ошибка запроса userinfo: {e}")
    data = resp.json()
    logger.debug("Yandex user info: %s", data)
    return data


async def fetch_vk_user_info(client, access_token: str) -> dict:
    """ Меняем токен VK API для получения инфы о юзере"""
    params = {
        "access_token": access_token,
        "v": settings.vk_api_version,
        "fields": "verified,sex,screen_name,email"
    }
    resp = await client.get(
        settings.vk_api_base_url + "users.get",
        params=params
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=resp.status_code, detail=f"Ошибка запроса userinfo: {e}")
    data = resp.json()
    logger.debug("VK user info: %s", data)
    if "response" in data and isinstance(data["response"], list) and len(data["response"]) > 0:
        return data["response"][0]
    else:
        raise HTTPException(status_code=400, detail="Не удалось получить информацию о пользователе из VK")


async def get_oauth_user_info(provider: str, client, token: dict) -> dict:
    """
    Выбираем функцию получения инфы о юзере в зависимости от провайдера.
    Если провайдер не распознан, возвращает исходный token."""
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"Нет access_token в ответе {provider.capitalize()}")

    if provider == "yandex":
        return await fetch_yandex_user_info(client, access_token)
    elif provider == "vk":
        return await fetch_vk_user_info(client, access_token)
    else:
        return token
