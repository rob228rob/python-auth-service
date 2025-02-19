import os
import json
import time
import logging
from kafka import KafkaConsumer
from telegram import Bot
from telegram.error import InvalidToken

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
NOTIFY_TOPIC = os.getenv('NOTIFY_TOPIC', 'user_notifications')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '******')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '******')

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не задан!")
    exit(1)

# fail fast
try:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("Telegram Bot успешно инициализирован.")
except InvalidToken as e:
    logger.error(f"Неверный токен Telegram: {e}")
    exit(1)
except Exception as e:
    logger.error(f"Ошибка при инициализации Telegram Bot: {e}")
    exit(1)

# Инициализация Kafka Consumer
consumer = KafkaConsumer(
    NOTIFY_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id='telegram_notifier_group',
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def send_to_tg_chat(data):
    """
    Отправляет сообщение в Telegram. Если data не является словарем,
    оборачивает его в словарь с ключами 'username' и 'message' """
    if not isinstance(data, dict):
        logger.warning("Полученное сообщение не является dict, оборачиваю его в словарь")
        data = {"username": "пользователь", "message": str(data)}
    text = f"Привет, {data.get('username', 'пользователь')}! {data.get('message', '')}"
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        logger.info("Отправлено сообщение в Telegram: %s", text)
    except Exception as e:
        logger.error("Ошибка отправки сообщения в Telegram: %s", e)

def consume_messages():
    logger.info("Kafka Consumer запущен и слушает топик '%s'", NOTIFY_TOPIC)
    for message in consumer:
        logger.debug("Получено сообщение: %s", message)
        data = message.value
        send_to_tg_chat(data)

if __name__ == "__main__":
    logger.info("Запуск Kafka Consumer...")
    try:
        consume_messages()
    except KeyboardInterrupt:
        logger.info("Консьюмер остановлен пользователем.")
    except Exception as e:
        logger.error("Консьюмер столкнулся с ошибкой: %s", e, exc_info=True)
        time.sleep(5)
