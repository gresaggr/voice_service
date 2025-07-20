from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional


class UserBase(BaseModel):
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    username: Optional[str] = Field(None, description="Username в Telegram")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя")


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    balance: Decimal = Field(default=Decimal('0.00'), description="Начальный баланс")
    
    @validator('balance')
    def validate_balance(cls, v):
        if v < 0:
            raise ValueError('Баланс не может быть отрицательным при создании')
        return v


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    balance: Optional[Decimal] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Схема для ответа с данными пользователя"""
    id: int
    balance: Decimal
    is_active: bool
    is_premium: bool
    registration_date: datetime
    last_activity: Optional[datetime]
    last_free_usage: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Расширенная схема профиля пользователя"""
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    balance: Decimal
    is_active: bool
    is_premium: bool
    registration_date: datetime
    last_activity: Optional[datetime]
    last_free_usage: Optional[datetime]
    total_requests: int = Field(default=0)
    successful_requests: int = Field(default=0)
    total_spent: Decimal = Field(default=Decimal('0.00'))
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """Статистика пользователя"""
    user_id: int
    period_days: int
    total_requests: int
    successful_requests: int
    success_rate: float
    total_spent: Decimal
    total_deposits: Decimal
    free_usages: int
    
    @validator('success_rate')
    def validate_success_rate(cls, v):
        return round(v, 2)


class UserBalanceInfo(BaseModel):
    """Информация о балансе пользователя"""
    telegram_id: int
    current_balance: Decimal
    can_use_service: bool
    time_until_free_usage: Optional[float] = Field(None, description="Часов до бесплатного использования")
    
    @validator('current_balance')
    def validate_balance(cls, v):
        return round(v, 2)