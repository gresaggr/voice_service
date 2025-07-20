"""
Кастомные фильтры для телеграм бота
"""
from typing import Union, Dict, Any
from datetime import datetime, timedelta

from aiogram import types
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import get_session
from app.services.user_service import UserService
from app.services.balance_service import BalanceService
from app.utils.constants import ADMIN_IDS


class IsRegisteredFilter(BaseFilter):
    """Фильтр для проверки регистрации пользователя"""
    
    async def __call__(self, message: types.Message) -> bool:
        async with get_session() as session:
            user_service = UserService(session)
            user = await user_service.get_by_telegram_id(message.from_user.id)
            return user is not None


class IsAdminFilter(BaseFilter):
    """Фильтр для проверки администратора"""
    
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMIN_IDS


class HasPositiveBalanceFilter(BaseFilter):
    """Фильтр для проверки положительного баланса"""
    
    async def __call__(self, message: types.Message) -> bool:
        async with get_session() as session:
            balance_service = BalanceService(session)
            balance = await balance_service.get_user_balance(message.from_user.id)
            return balance > 0


class CanUseServiceFilter(BaseFilter):
    """Фильтр для проверки возможности использования сервиса"""
    
    async def __call__(self, message: types.Message) -> Union[bool, Dict[str, Any]]:
        async with get_session() as session:
            user_service = UserService(session)
            balance_service = BalanceService(session)
            
            user = await user_service.get_by_telegram_id(message.from_user.id)
            if not user:
                return False
                
            balance = await balance_service.get_user_balance(message.from_user.id)
            
            # Если баланс положительный - можно использовать
            if balance > 0:
                return True
                
            # Если баланс отрицательный - проверяем последнее использование
            last_usage = await user_service.get_last_service_usage(user.id)
            
            if not last_usage:
                return True  # Первое использование
                
            # Проверяем прошли ли сутки с последнего использования
            time_diff = datetime.utcnow() - last_usage
            if time_diff >= timedelta(hours=24):
                return True
                
            # Вычисляем сколько часов осталось
            hours_left = 24 - int(time_diff.total_seconds() // 3600)
            
            return {
                "can_use": False,
                "hours_left": hours_left
            }