from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from app.utils.constants import TransactionType, PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    """Схема для создания платежа"""
    user_id: int
    amount: Decimal = Field(..., gt=0, description="Сумма платежа")
    payment_method: PaymentMethod = Field(..., description="Метод платежа")
    description: Optional[str] = Field(None, description="Описание платежа")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма платежа должна быть больше 0')
        if v > Decimal('100000.00'):
            raise ValueError('Сумма платежа не может превышать 100,000')
        return round(v, 2)


class PaymentUpdate(BaseModel):
    """Схема для обновления платежа"""
    status: Optional[PaymentStatus] = None
    payment_id: Optional[str] = None
    payment_url: Optional[str] = None
    confirmation_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class PaymentResponse(BaseModel):
    """Схема ответа с данными платежа"""
    id: int
    user_id: int
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    payment_id: Optional[str]
    payment_url: Optional[str]
    description: Optional[str]
    confirmation_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        use_enum_values = True


class BalanceTransactionCreate(BaseModel):
    """Схема для создания транзакции баланса"""
    user_id: int
    amount: Decimal = Field(..., description="Сумма транзакции (положительная для пополнения, отрицательная для списания)")
    transaction_type: TransactionType
    description: str = Field(..., description="Описание транзакции")
    payment_method: Optional[str] = Field(None, description="Метод платежа для пополнений")
    reference_id: Optional[int] = Field(None, description="ID связанной записи (платеж, использование услуги)")


class BalanceTransactionResponse(BaseModel):
    """Схема ответа с данными транзакции баланса"""
    id: int
    user_id: int
    amount: Decimal
    transaction_type: TransactionType
    description: str
    payment_method: Optional[str]
    reference_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class YumoneyPaymentData(BaseModel):
    """Данные для создания платежа через ЮMoney"""
    amount: Decimal
    description: str
    return_url: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        return round(v, 2)


class TelegramStarsPaymentData(BaseModel):
    """Данные для создания платежа через Telegram Stars"""
    amount: int = Field(..., gt=0, description="Количество звезд")
    description: str = Field(..., description="Описание товара")
    payload: Optional[str] = Field(None, description="Полезная нагрузка")
    
    @validator('amount')
    def validate_stars_amount(cls, v):
        if v < 1:
            raise ValueError('Количество звезд должно быть больше 0')
        if v > 2500:
            raise ValueError('Максимальное количество звезд за одну транзакцию: 2500')
        return v


class PaymentVerificationData(BaseModel):
    """Данные для верификации платежа"""
    payment_id: str
    payment_method: PaymentMethod
    verification_data: Dict[str, Any] = Field(default_factory=dict)


class PaymentStatusResponse(BaseModel):
    """Ответ со статусом платежа"""
    payment_id: str
    status: PaymentStatus
    amount: Optional[Decimal] = None
    paid_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        use_enum_values = True


class RefundCreate(BaseModel):
    """Схема для создания возврата"""
    payment_id: int
    amount: Optional[Decimal] = Field(None, description="Сумма возврата (если не указана, возвращается вся сумма)")
    reason: str = Field(..., description="Причина возврата")
    
    @validator('amount')
    def validate_refund_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Сумма возврата должна быть больше 0')
        return v


class PaymentMethodInfo(BaseModel):
    """Информация о методе платежа"""
    method: PaymentMethod
    display_name: str
    description: str
    min_amount: Decimal
    max_amount: Decimal
    is_available: bool = True
    processing_fee: Optional[Decimal] = None
    
    class Config:
        use_enum_values = True


class PaymentSummary(BaseModel):
    """Сводка платежей пользователя"""
    user_id: int
    total_payments: int
    total_amount: Decimal
    successful_payments: int
    successful_amount: Decimal
    pending_payments: int
    pending_amount: Decimal
    failed_payments: int
    last_payment_date: Optional[datetime]
    
    @validator('total_amount', 'successful_amount', 'pending_amount')
    def validate_decimal_amounts(cls, v):
        return round(v, 2)