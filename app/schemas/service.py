from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from app.utils.constants import RequestStatus


class ServiceCategory(BaseModel):
    """Категория услуг"""
    name: str = Field(..., description="Название категории")
    display_name: str = Field(..., description="Отображаемое название")
    description: Optional[str] = Field(None, description="Описание категории")
    icon: Optional[str] = Field(None, description="Иконка категории")
    cost: Decimal = Field(..., description="Стоимость услуги в этой категории")


class ServiceSubcategory(BaseModel):
    """Подкатегория услуг"""
    name: str = Field(..., description="Название подкатегории")
    display_name: str = Field(..., description="Отображаемое название")
    description: Optional[str] = Field(None, description="Описание подкатегории")
    category: str = Field(..., description="Родительская категория")
    examples: Optional[List[str]] = Field(None, description="Примеры использования")


class VoiceRequestCreate(BaseModel):
    """Схема для создания голосового запроса"""
    user_id: int
    category: str = Field(..., description="Категория услуги")
    subcategory: str = Field(..., description="Подкатегория услуги")
    file_path: str = Field(..., description="Путь к голосовому файлу")
    file_duration: Optional[int] = Field(None, description="Длительность файла в секундах")
    
    @validator('file_duration')
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Длительность файла должна быть больше 0')
        return v


class VoiceRequestUpdate(BaseModel):
    """Схема для обновления голосового запроса"""
    status: Optional[RequestStatus] = None
    result_text: Optional[str] = None
    processing_time: Optional[int] = None
    error_message: Optional[str] = None


class VoiceRequestResponse(BaseModel):
    """Схема ответа с данными голосового запроса"""
    id: int
    user_id: int
    category: str
    subcategory: str
    file_path: str
    file_duration: Optional[int]
    status: RequestStatus
    result_text: Optional[str]
    processing_time: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ServiceUsageCreate(BaseModel):
    """Схема для создания записи об использовании услуги"""
    user_id: int
    category: str
    subcategory: str
    cost: Decimal
    is_free: bool = Field(default=False)
    
    @validator('cost')
    def validate_cost(cls, v):
        if v < 0:
            raise ValueError('Стоимость не может быть отрицательной')
        return v


class ServiceUsageResponse(BaseModel):
    """Схема ответа с данными об использовании услуги"""
    id: int
    user_id: int
    category: str
    subcategory: str
    cost: Decimal
    is_free: bool
    used_at: datetime
    
    class Config:
        from_attributes = True


class ServiceStatistics(BaseModel):
    """Статистика по категории услуг"""
    category: str
    usage_count: int
    total_revenue: Decimal
    average_cost: Decimal
    success_rate: float
    
    @validator('average_cost', 'total_revenue')
    def validate_decimal(cls, v):
        return round(v, 2)
    
    @validator('success_rate')
    def validate_success_rate(cls, v):
        return round(v, 2)


class ProcessingResult(BaseModel):
    """Результат обработки голосового сообщения"""
    request_id: int
    status: RequestStatus
    result_text: Optional[str] = None
    processing_time: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ServiceConfig(BaseModel):
    """Конфигурация сервиса"""
    categories: List[ServiceCategory]
    subcategories: List[ServiceSubcategory]
    default_cost: Decimal = Field(default=Decimal('10.00'))
    max_file_duration: int = Field(default=300, description="Максимальная длительность файла в секундах")
    free_usage_cooldown_hours: int = Field(default=24, description="Период ожидания для бесплатного использования")
    
    @validator('max_file_duration')
    def validate_max_duration(cls, v):
        if v <= 0:
            raise ValueError('Максимальная длительность должна быть больше 0')
        return v
    
    @validator('free_usage_cooldown_hours')
    def validate_cooldown(cls, v):
        if v <= 0:
            raise ValueError('Период ожидания должен быть больше 0')
        return v