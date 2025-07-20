from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.config import settings


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Создать нового пользователя."""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
    
    async def update_balance(self, user_id: int, amount: Decimal) -> bool:
        """Обновить баланс пользователя."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance=User.balance + amount)
        )
        return result.rowcount > 0
    
    async def update_profile(self, user_id: int, **kwargs) -> bool:
        """Обновить профиль пользователя."""
        if not kwargs:
            return False
        
        kwargs['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
        )
        return result.rowcount > 0 > 0
    
    @staticmethod
    async def can_use_free_service(user: User) -> bool:
        """Проверить, может ли пользователь использовать бесплатную услугу."""
        if user.balance >= Decimal(str(settings.service_cost)):
            return False  # Если есть баланс, не используем бесплатную услугу
        
        if not user.last_free_usage:
            return True  # Первое использование
        
        time_since_last_use = datetime.utcnow() - user.last_free_usage
        return time_since_last_use >= timedelta(hours=settings.free_usage_hours)
    
    @staticmethod
    async def get_time_until_free_usage(user: User) -> Optional[timedelta]:
        """Получить время до следующего бесплатного использования."""
        if not user.last_free_usage:
            return None
        
        next_free_time = user.last_free_usage + timedelta(hours=settings.free_usage_hours)
        now = datetime.utcnow()
        
        if now >= next_free_time:
            return None
        
        return next_free_time - now
    
    async def mark_free_usage(self, user_id: int) -> bool:
        """Отметить использование бесплатной услуги."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_free_usage=datetime.utcnow())
        )
        return result.rowcount > 0
    
    async def deduct_balance(self, user_id: int, amount: Decimal) -> bool:
        """Списать средства с баланса."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id, User.balance >= amount)
            .values(balance=User.balance - amount)
        )
        return result.rowcount