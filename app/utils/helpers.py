"""
Вспомогательные функции
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from decimal import Decimal, ROUND_HALF_UP

from .constants import (
    SERVICE_PRICES, 
    FREE_USAGE_LIMIT_HOURS, 
    STARS_TO_RUB_RATE,
    DEFAULT_TIMEZONE
)


def format_currency(amount: Union[float, Decimal], currency: str = "RUB") -> str:
    """Форматирование валюты"""
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    
    # Округляем до 2 знаков после запятой
    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    if currency == "RUB":
        return f"{amount:.2f} ₽"
    elif currency == "STARS":
        return f"{int(amount)} ⭐"
    else:
        return f"{amount:.2f} {currency}"


def calculate_service_price(category: str, subcategory: str) -> float:
    """Вычисление цены услуги"""
    if category not in SERVICE_PRICES:
        return 0.0
    
    if subcategory not in SERVICE_PRICES[category]:
        return 0.0
    
    return SERVICE_PRICES[category][subcategory]


def calculate_time_until_next_free_use(last_free_use: datetime) -> Optional[timedelta]:
    """
    Вычисление времени до следующего бесплатного использования
    
    Returns:
        timedelta если нужно ждать, None если можно использовать
    """
    if not last_free_use:
        return None
    
    now = datetime.utcnow()
    next_free_use = last_free_use + timedelta(hours=FREE_USAGE_LIMIT_HOURS)
    
    if now >= next_free_use:
        return None
    
    return next_free_use - now


def format_time_remaining(td: timedelta) -> str:
    """Форматирование оставшегося времени"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours} ч. {minutes} мин."
    else:
        return f"{minutes} мин."


def convert_stars_to_rubles(stars: int) -> float:
    """Конвертация Telegram Stars в рубли"""
    return stars * STARS_TO_RUB_RATE


def convert_rubles_to_stars(rubles: float) -> int:
    """Конвертация рублей в Telegram Stars"""
    return int(rubles / STARS_TO_RUB_RATE)


def generate_payment_id() -> str:
    """Генерация уникального ID платежа"""
    timestamp = str(int(datetime.utcnow().timestamp()))
    random_part = secrets.token_hex(8)
    return f"pay_{timestamp}_{random_part}"


def generate_order_id() -> str:
    """Генерация ID заказа"""
    timestamp = str(int(datetime.utcnow().timestamp()))
    random_part = secrets.token_hex(4)
    return f"order_{timestamp}_{random_part}"


def create_payment_hash(payment_data: Dict[str, Any], secret_key: str) -> str:
    """Создание хеша для проверки платежа"""
    # Сортируем ключи для стабильного хеша
    sorted_items = sorted(payment_data.items())
    data_string = "&".join([f"{k}={v}" for k, v in sorted_items])
    data_string += f"&secret={secret_key}"
    
    return hashlib.sha256(data_string.encode()).hexdigest()


def verify_payment_hash(payment_data: Dict[str, Any], received_hash: str, secret_key: str) -> bool:
    """Проверка хеша платежа"""
    expected_hash = create_payment_hash(payment_data, secret_key)
    return secrets.compare_digest(expected_hash, received_hash)


def format_user_info(user_data: Dict[str, Any]) -> str:
    """Форматирование информации о пользователе"""
    lines = []
    
    if user_data.get('username'):
        lines.append(f"👤 Имя: {user_data['username']}")
    
    if user_data.get('telegram_id'):
        lines.append(f"🆔 Telegram ID: {user_data['telegram_id']}")
    
    if user_data.get('balance') is not None:
        lines.append(f"💰 Баланс: {format_currency(user_data['balance'])}")
    
    if user_data.get('created_at'):
        created_date = user_data['created_at'].strftime('%d.%m.%Y')
        lines.append(f"📅 Регистрация: {created_date}")
    
    return "\n".join(lines)


def format_service_info(category: str, subcategory: str) -> str:
    """Форматирование информации об услуге"""
    from .constants import SERVICE_CATEGORIES, SERVICE_SUBCATEGORIES
    
    category_name = SERVICE_CATEGORIES.get(category, category)
    subcategory_name = SERVICE_SUBCATEGORIES.get(category, {}).get(subcategory, subcategory)
    price = calculate_service_price(category, subcategory)
    
    return f"{category_name} → {subcategory_name}\n💰 Цена: {format_currency(price)}"


def extract_file_id_from_message(message_data: Dict[str, Any]) -> Optional[str]:
    """Извлечение file_id из данных сообщения"""
    if 'voice' in message_data and message_data['voice'].get('file_id'):
        return message_data['voice']['file_id']
    
    if 'audio' in message_data and message_data['audio'].get('file_id'):
        return message_data['audio']['file_id']
    
    return None


def create_callback_data(prefix: str, **kwargs) -> str:
    """Создание callback data"""
    parts = [prefix]
    for key, value in kwargs.items():
        parts.append(f"{key}:{value}")
    
    data = "|".join(parts)
    
    # Проверяем лимит Telegram (64 байта)
    if len(data.encode('utf-8')) > 64:
        # Сокращаем данные если необходимо
        truncated = data[:60] + "..."
        return truncated
    
    return data


def parse_callback_data(data: str) -> Dict[str, str]:
    """Парсинг callback data"""
    parts = data.split("|")
    result = {"prefix": parts[0]}
    
    for part in parts[1:]:
        if ":" in part:
            key, value = part.split(":", 1)
            result[key] = value
    
    return result


async def safe_delete_message(bot, chat_id: int, message_id: int) -> bool:
    """Безопасное удаление сообщения"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except Exception:
        return False


async def retry_async_operation(
    operation,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """Повторение асинхронной операции с экспоненциальной задержкой"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (backoff_factor ** attempt))
    
    raise last_exception


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Обрезание текста с добавлением суффикса"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_current_moscow_time() -> datetime:
    """Получение текущего времени в московской временной зоне"""
    from datetime import timezone
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)


def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Форматирование даты и времени"""
    if dt.tzinfo is None:
        # Если нет информации о временной зоне, добавляем московское время
        moscow_tz = timezone(timedelta(hours=3))
        dt = dt.replace(tzinfo=moscow_tz)
    
    return dt.strftime(format_str)