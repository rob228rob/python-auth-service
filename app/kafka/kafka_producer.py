# app/kafka_producer.py
import json
import logging
import os

from kafka import KafkaProducer

logger = logging.getLogger(__name__)
KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Инициализация с гарантией At Least Once
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    acks='all',
    retries=5,
    max_in_flight_requests_per_connection=5,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def handle_producer_result(msg):
    logger.info(f"Сообщение доставлено")

def handle_producer_error(err):
    logger.error(f"Ошибка доставки сообщения: {err}")

def send_message(key: str, message: dict, topic: str = 'notifications_topic'):
    try:
        if key is not None and isinstance(key, str):
            key = key.encode('utf-8')
        future = producer.send(topic=topic, key=key, value=message)
        future.add_callback(handle_producer_result)
        logger.info(f"Sending msg to kafka with k: ${key} msg: ${message}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise e