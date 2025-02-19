# app/config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_access_secret: str = os.getenv("JWT_ACCESS_SECRET", "FIXME")
    jwt_refresh_secret: str = os.getenv("JWT_REFRESH_SECRET", "FIXME")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 10080
    refresh_token_expire_days: int = 7

    # Настройка кредов для серверов по oauth
    yandex_client_id: str = os.getenv("YANDEX_CLIENT_ID", "FIXME")
    yandex_client_secret: str = os.getenv("YANDEX_CLIENT_SECRET", "FIXME")

    vk_client_id: str = os.getenv("VK_CLIENT_ID", "FIXME")
    vk_client_secret: str = os.getenv("VK_CLIENT_SECRET", "FIXME")
    vk_authorize_url: str = os.getenv("VK_AUTHORIZE_URL", "https://oauth.vk.com/authorize")
    vk_token_endpoint: str = os.getenv("VK_TOKEN_ENDPOINT", "https://oauth.vk.com/access_token")
    vk_api_base_url: str = os.getenv("VK_API_BASE_URL", "https://api.vk.com/method/")
    vk_api_version: str = os.getenv("VK_API_VERSION", "5.131")
    vk_scope: str = os.getenv("VK_SCOPE", "email")


    yandex_oauth_user_info_url: str = os.getenv("YANDEX_OAUTH_USER_INFO_URL", "https://login.yandex.ru/info")

    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/app_db")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    notify_topic: str = os.getenv("NOTIFY_TOPIC", "user_notifications")

    class Config:
        env_file = ".env"


settings = Settings()
