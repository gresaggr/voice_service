from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy import select

from app.database.engine import db_manager
from app.database.models import User
from app.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки регистрации пользователя."""
    
    def __init__(self, skip_registration_check: bool = False):
        self.skip_registration_check = skip_registration_check
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем telegram_id из события
        telegram_id = None
        if isinstance(event, (Message, CallbackQuery)):
            telegram_id = event.from_user.id
        
        if not telegram_id:
            return await handler(event, data)
        
        # Получаем или создаём пользователя
        async with db_manager.get_session() as session:
            user_service = UserService(session)
            
            # Проверяем, существует ли пользователь
            user = await user_service.get_by_telegram_id(telegram_id)
            
            if not user and not self.skip_registration_check:
                # Пользователь не зарегистрирован, создаём базовую запись
                user_data = {
                    'telegram_id': telegram_id,
                    'username': getattr(event.from_user, 'username', None),
                    'first_name': getattr(event.from_user, 'first_name', None),
                    'last_name': getattr(event.from_user, 'last_name', None),
                }
                user = await user_service.create_user(user_data)
            
            # Добавляем пользователя в данные для обработчика
            data['user'] = user
            data['user_service'] = user_service
        
        return await handler(event, data)


class RegistrationRequiredMiddleware(BaseMiddleware):
    """Middleware для проверки обязательной регистрации."""
    
    def __init__(self, registration_handlers: list[str] = None):
        # Обработчики, для которых не требуется регистрация
        self.registration_handlers = registration_handlers or [
            'start_handler',
            'registration_start',
            'registration_complete'
        ]
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Пропускаем проверку для обработчиков регистрации
        handler_name = handler.__name__
        if handler_name in self.registration_handlers:
            return await handler(event, data)
        
        user = data.get('user')
        
        if not user:
            # Перенаправляем на регистрацию
            if isinstance(event, Message):
                await event.answer(
                    "🚫 Для использования бота необходимо зарегистрироваться.\n"
                    "Используйте команду /start"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "Необходимо зарегистрироваться",
                    show_alert=True
                )
            return
        
        return await handler(event, data)