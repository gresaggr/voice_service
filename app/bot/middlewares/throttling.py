import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для защиты от спама."""
    
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_buckets: Dict[int, float] = {}
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем user_id из события
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        
        if not user_id:
            return await handler(event, data)
        
        current_time = time.time()
        last_request_time = self.user_buckets.get(user_id, 0)
        
        # Проверяем, прошло ли достаточно времени
        if current_time - last_request_time < self.rate_limit:
            # Слишком частые запросы
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Пожалуйста, не отправляйте сообщения так часто."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "Не нажимайте кнопки так часто",
                    show_alert=True
                )
            return
        
        # Обновляем время последнего запроса
        self.user_buckets[user_id] = current_time
        
        # Очищаем старые записи (старше 1 часа)
        cutoff_time = current_time - 3600
        self.user_buckets = {
            uid: timestamp 
            for uid, timestamp in self.user_buckets.items() 
            if timestamp > cutoff_time
        }
        
        return await handler(event, data)