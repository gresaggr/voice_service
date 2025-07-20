from aiogram import Router
from aiogram.types import Message

from app.services.user_service import UserService

registration_router = Router()


@registration_router.message()
async def auto_registration_handler(message: Message, user: any = None, user_service: UserService = None):
    """Auto-registration handler for new users."""
    
    # This handler is triggered by AuthMiddleware for new users
    # The user creation is handled in the middleware
    
    if user is None:
        welcome_text = (
            "🎉 Регистрация завершена!\n\n"
            f"Добро пожаловать, {message.from_user.first_name or 'пользователь'}!\n\n"
            "Теперь вы можете пользоваться всеми функциями сервиса.\n"
            "Используйте команду /start для начала работы."
        )
        
        await message.answer(welcome_text)
        return
    
    # If user already exists, this won't be triggered