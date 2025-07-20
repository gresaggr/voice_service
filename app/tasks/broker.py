from taskiq import AsyncBroker
from taskiq_aio_pika import AioPikaBroker

from app.config import settings

# Создаём брокер для RabbitMQ
broker = AioPikaBroker(settings.rabbitmq_url)


# В TaskIQ используется startup/shutdown через декораторы задач
async def startup_hook():
    """Функция запуска брокера"""
    print("TaskIQ broker started successfully")


async def shutdown_hook():
    """Функция остановки брокера"""
    print("TaskIQ broker shut down")


# Или можно использовать middleware
class BrokerMiddleware:
    async def pre_send(self, message):
        pass

    async def post_send(self, message):
        pass
